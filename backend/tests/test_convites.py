"""Aceite de convite: conta nova define a senha; conta existente entra pelo login normal e nada é redefinido."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Convite, Empresa, Usuario, UsuarioEmpresa
from app.routers.auth import _criar_token_parcial
from app.security import criar_token, gerar_hash, verificar_senha
from tests.conftest import SENHA

API = "/api/v1"
SENHA_NOVA = "outra-senha-forte-456"


async def _empresa(sessao: AsyncSession, nome: str = "Empresa Convite") -> Empresa:
    empresa = Empresa(nome=nome)
    sessao.add(empresa)
    await sessao.commit()
    return empresa


async def _usuario(
    sessao: AsyncSession, email: str, *, ativo: bool = True, totp: bool = False
) -> Usuario:
    usuario = Usuario(
        email=email, nome=email.split("@")[0], admin=False, senha_hash=gerar_hash(SENHA), ativo=ativo,
        totp_ativo=totp, totp_secret="JBSWY3DPEHPK3PXP" if totp else None,
    )
    sessao.add(usuario)
    await sessao.commit()
    return usuario


async def _convite(
    sessao: AsyncSession,
    empresa: Empresa,
    criador: Usuario,
    email: str,
    *,
    papel: str = "membro",
    expira_em: datetime | None = None,
    usado_em: datetime | None = None,
) -> Convite:
    convite = Convite(
        email=email,
        empresa_id=empresa.id,
        papel=papel,
        criado_por=criador.id,
        expira_em=expira_em or datetime.now(UTC) + timedelta(hours=72),
        usado_em=usado_em,
    )
    sessao.add(convite)
    await sessao.commit()
    await sessao.refresh(convite)
    return convite


async def _entrar(http: AsyncClient, email: str) -> dict[str, str]:
    r = await http.post(f"{API}/auth/login", json={"email": email, "senha": SENHA})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _aceitar(http: AsyncClient, convite: Convite, corpo: dict | None = None, headers: dict | None = None):
    return await http.post(f"{API}/auth/convite/{convite.token}/aceitar", json=corpo or {}, headers=headers or {})


async def _membership(sessao: AsyncSession, empresa: Empresa, usuario: Usuario) -> UsuarioEmpresa | None:
    return await sessao.get(UsuarioEmpresa, (empresa.id, usuario.id), populate_existing=True)


@pytest.fixture
async def cenario(sessao: AsyncSession) -> tuple[Empresa, Usuario]:
    """Empresa e o administrador que emite os convites."""
    empresa = await _empresa(sessao)
    criador = await _usuario(sessao, "criador@empresa.com")
    return empresa, criador


# ---------------------------------------------------------------- informações públicas do convite


async def test_info_do_convite_para_email_sem_conta(http: AsyncClient, sessao: AsyncSession, cenario):
    empresa, criador = cenario
    convite = await _convite(sessao, empresa, criador, "novo@empresa.com")
    r = await http.get(f"{API}/auth/convite/{convite.token}")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["estado"] == "valido" and corpo["conta_existente"] is False
    assert corpo["email"] == "novo@empresa.com"


async def test_info_do_convite_para_email_com_conta(http: AsyncClient, sessao: AsyncSession, cenario):
    empresa, criador = cenario
    await _usuario(sessao, "ja.tem@empresa.com")
    convite = await _convite(sessao, empresa, criador, "ja.tem@empresa.com")
    r = await http.get(f"{API}/auth/convite/{convite.token}")
    assert r.status_code == 200 and r.json()["conta_existente"] is True


# ---------------------------------------------------------------- conta nova


async def test_conta_nova_aceita_define_senha_e_entra_com_o_papel_do_convite(
    http: AsyncClient, sessao: AsyncSession, cenario
):
    empresa, criador = cenario
    convite = await _convite(sessao, empresa, criador, "novo@empresa.com", papel="admin")
    r = await _aceitar(http, convite, {"senha": SENHA_NOVA, "confirmar_senha": SENHA_NOVA})
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]

    usuario = await sessao.scalar(select(Usuario).where(Usuario.email == "novo@empresa.com"))
    assert usuario is not None and verificar_senha(SENHA_NOVA, usuario.senha_hash)
    membership = await _membership(sessao, empresa, usuario)
    assert membership is not None and membership.ativo and membership.papel == "admin"
    await sessao.refresh(convite)
    assert convite.usado_em is not None


async def test_conta_nova_com_senhas_diferentes_e_recusada(http: AsyncClient, sessao: AsyncSession, cenario):
    empresa, criador = cenario
    convite = await _convite(sessao, empresa, criador, "novo@empresa.com")
    r = await _aceitar(http, convite, {"senha": SENHA_NOVA, "confirmar_senha": "diferente-123456"})
    assert r.status_code == 422 and "não conferem" in r.json()["erro"]["mensagem"]
    assert await sessao.scalar(select(Usuario).where(Usuario.email == "novo@empresa.com")) is None


async def test_conta_nova_sem_senha_e_recusada(http: AsyncClient, sessao: AsyncSession, cenario):
    empresa, criador = cenario
    convite = await _convite(sessao, empresa, criador, "novo@empresa.com")
    r = await _aceitar(http, convite, {})
    assert r.status_code == 422
    assert await sessao.scalar(select(Usuario).where(Usuario.email == "novo@empresa.com")) is None


async def test_conta_nova_ignora_token_invalido_no_cabecalho(http: AsyncClient, sessao: AsyncSession, cenario):
    """Um token velho guardado no navegador não pode impedir quem ainda não tem conta de aceitar."""
    empresa, criador = cenario
    convite = await _convite(sessao, empresa, criador, "novo@empresa.com")
    r = await _aceitar(
        http, convite, {"senha": SENHA_NOVA, "confirmar_senha": SENHA_NOVA}, {"Authorization": "Bearer lixo"}
    )
    assert r.status_code == 200, r.text


async def test_convite_expirado_e_recusado(http: AsyncClient, sessao: AsyncSession, cenario):
    empresa, criador = cenario
    convite = await _convite(
        sessao, empresa, criador, "novo@empresa.com", expira_em=datetime.now(UTC) - timedelta(hours=1)
    )
    r = await _aceitar(http, convite, {"senha": SENHA_NOVA, "confirmar_senha": SENHA_NOVA})
    assert r.status_code == 422 and "expirou" in r.json()["erro"]["mensagem"]


async def test_convite_ja_usado_e_recusado(http: AsyncClient, sessao: AsyncSession, cenario):
    empresa, criador = cenario
    convite = await _convite(sessao, empresa, criador, "novo@empresa.com", usado_em=datetime.now(UTC))
    r = await _aceitar(http, convite, {"senha": SENHA_NOVA, "confirmar_senha": SENHA_NOVA})
    assert r.status_code == 422 and "já foi utilizado" in r.json()["erro"]["mensagem"]


async def test_segundo_aceite_do_mesmo_convite_e_recusado(http: AsyncClient, sessao: AsyncSession, cenario):
    """Reuso sequencial do token. A serialização de aceites simultâneos vem do FOR UPDATE no serviço."""
    empresa, criador = cenario
    convite = await _convite(sessao, empresa, criador, "novo@empresa.com")
    corpo = {"senha": SENHA_NOVA, "confirmar_senha": SENHA_NOVA}
    assert (await _aceitar(http, convite, corpo)).status_code == 200
    segundo = await _aceitar(http, convite, corpo)
    assert segundo.status_code == 422 and "já foi utilizado" in segundo.json()["erro"]["mensagem"]
    total = await sessao.scalar(select(func.count()).select_from(Usuario).where(Usuario.email == "novo@empresa.com"))
    assert total == 1


# ---------------------------------------------------------------- conta existente


async def test_conta_existente_sem_autenticacao_nao_redefine_nada(http: AsyncClient, sessao: AsyncSession, cenario):
    """Regressão da falha original: o link do convite não pode trocar a senha de uma conta existente."""
    empresa, criador = cenario
    vitima = await _usuario(sessao, "vitima@empresa.com")
    hash_original = vitima.senha_hash
    convite = await _convite(sessao, empresa, criador, "vitima@empresa.com")

    r = await _aceitar(http, convite, {"senha": SENHA_NOVA, "confirmar_senha": SENHA_NOVA})

    assert r.status_code == 401
    await sessao.refresh(vitima)
    assert vitima.senha_hash == hash_original and vitima.ativo is True
    assert await _membership(sessao, empresa, vitima) is None
    await sessao.refresh(convite)
    assert convite.usado_em is None
    assert (await http.post(f"{API}/auth/login", json={"email": vitima.email, "senha": SENHA})).status_code == 200


async def test_conta_existente_com_token_invalido_e_tratada_como_anonima(
    http: AsyncClient, sessao: AsyncSession, cenario
):
    empresa, criador = cenario
    vitima = await _usuario(sessao, "vitima@empresa.com")
    convite = await _convite(sessao, empresa, criador, "vitima@empresa.com")
    r = await _aceitar(http, convite, headers={"Authorization": "Bearer lixo"})
    assert r.status_code == 401
    assert await _membership(sessao, empresa, vitima) is None


async def test_conta_existente_autenticada_como_outro_usuario_e_recusada(
    http: AsyncClient, sessao: AsyncSession, cenario
):
    empresa, criador = cenario
    alvo = await _usuario(sessao, "alvo@empresa.com")
    intruso = await _usuario(sessao, "intruso@empresa.com")
    convite = await _convite(sessao, empresa, criador, "alvo@empresa.com")

    r = await _aceitar(http, convite, headers=await _entrar(http, intruso.email))

    assert r.status_code == 403
    assert await _membership(sessao, empresa, alvo) is None
    assert await _membership(sessao, empresa, intruso) is None
    await sessao.refresh(convite)
    assert convite.usado_em is None


async def test_conta_existente_autenticada_como_dono_entra_sem_trocar_a_senha(
    http: AsyncClient, sessao: AsyncSession, cenario
):
    empresa, criador = cenario
    dono = await _usuario(sessao, "dono@empresa.com")
    hash_original = dono.senha_hash
    convite = await _convite(sessao, empresa, criador, "dono@empresa.com", papel="admin")

    r = await _aceitar(http, convite, headers=await _entrar(http, dono.email))

    assert r.status_code == 200, r.text
    membership = await _membership(sessao, empresa, dono)
    assert membership is not None and membership.ativo and membership.papel == "admin"
    await sessao.refresh(dono)
    assert dono.senha_hash == hash_original
    await sessao.refresh(convite)
    assert convite.usado_em is not None
    assert (await http.post(f"{API}/auth/login", json={"email": dono.email, "senha": SENHA})).status_code == 200


async def test_conta_existente_ignora_senha_enviada_no_corpo(http: AsyncClient, sessao: AsyncSession, cenario):
    empresa, criador = cenario
    dono = await _usuario(sessao, "dono@empresa.com")
    hash_original = dono.senha_hash
    convite = await _convite(sessao, empresa, criador, "dono@empresa.com")

    r = await _aceitar(
        http, convite, {"senha": SENHA_NOVA, "confirmar_senha": SENHA_NOVA}, await _entrar(http, dono.email)
    )

    assert r.status_code == 200, r.text
    await sessao.refresh(dono)
    assert dono.senha_hash == hash_original


async def test_conta_desativada_nao_e_reativada_pelo_convite(http: AsyncClient, sessao: AsyncSession, cenario):
    empresa, criador = cenario
    desativada = await _usuario(sessao, "fora@empresa.com")
    token = criar_token(desativada.id, desativada.versao_sessao)  # emitido antes da desativação
    desativada.ativo = False
    await sessao.commit()
    convite = await _convite(sessao, empresa, criador, "fora@empresa.com")

    r = await _aceitar(http, convite, headers={"Authorization": f"Bearer {token}"})

    assert r.status_code == 401
    await sessao.refresh(desativada)
    assert desativada.ativo is False
    assert await _membership(sessao, empresa, desativada) is None


async def test_reconvite_reativa_membership_removida_com_o_novo_papel(
    http: AsyncClient, sessao: AsyncSession, cenario
):
    empresa, criador = cenario
    voltando = await _usuario(sessao, "voltando@empresa.com")
    sessao.add(UsuarioEmpresa(empresa_id=empresa.id, usuario_id=voltando.id, papel="membro", ativo=False))
    await sessao.commit()
    convite = await _convite(sessao, empresa, criador, "voltando@empresa.com", papel="admin")

    r = await _aceitar(http, convite, headers=await _entrar(http, voltando.email))

    assert r.status_code == 200, r.text
    membership = await _membership(sessao, empresa, voltando)
    assert membership is not None and membership.ativo and membership.papel == "admin"


async def test_aceite_nao_contorna_o_2fa(http: AsyncClient, sessao: AsyncSession, cenario):
    """Com 2FA ativo, só o token completo (pós-código) vale; o token parcial do login nunca autentica o aceite."""
    empresa, criador = cenario
    protegido = await _usuario(sessao, "protegido@empresa.com", totp=True)
    convite = await _convite(sessao, empresa, criador, "protegido@empresa.com")

    login = await http.post(f"{API}/auth/login", json={"email": protegido.email, "senha": SENHA})
    assert login.status_code == 200 and login.json().get("requer_2fa") is True
    assert "access_token" not in login.json()

    for parcial in (login.json()["token_temporario"], _criar_token_parcial(protegido.id)):
        r = await _aceitar(http, convite, headers={"Authorization": f"Bearer {parcial}"})
        assert r.status_code == 401
    assert await _membership(sessao, empresa, protegido) is None
    await sessao.refresh(convite)
    assert convite.usado_em is None

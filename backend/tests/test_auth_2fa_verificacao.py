"""Segundo fator no login: token parcial, tentativas limitadas e invalidação após 5 erros."""

import pyotp
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Usuario
from app.ratelimit import controle_token_parcial, limitador_de_2fa, limitador_de_login
from app.routers.auth_2fa import TotpBackupCode
from app.security import criar_token, gerar_hash
from app.services.totp import criptografar_segredo, gerar_segredo
from tests.conftest import SENHA

API = "/api/v1"
CODIGO_BACKUP = "a1b2c3d4e5f6"


@pytest.fixture(autouse=True)
def _limpar_limitadores():  # noqa: ANN202
    for lim in (limitador_de_login, limitador_de_2fa):
        lim._falhas.clear()
    controle_token_parcial._erros.clear()
    controle_token_parcial._revogados.clear()
    yield


@pytest_asyncio.fixture
async def usuario_2fa(sessao: AsyncSession) -> tuple[Usuario, str]:
    segredo = gerar_segredo()
    u = Usuario(
        email="com2fa@isolutis.com.br",
        nome="Com 2FA",
        senha_hash=gerar_hash(SENHA),
        totp_secret=criptografar_segredo(segredo),
        totp_ativo=True,
    )
    sessao.add(u)
    await sessao.flush()
    sessao.add(TotpBackupCode(usuario_id=u.id, codigo_hash=gerar_hash(CODIGO_BACKUP)))
    await sessao.commit()
    return u, segredo


async def _login_parcial(http: AsyncClient, usuario: Usuario) -> str:
    r = await http.post(f"{API}/auth/login", json={"email": usuario.email, "senha": SENHA})
    assert r.status_code == 200 and r.json()["requer_2fa"] is True
    assert "access_token" not in r.json()
    return r.json()["token_temporario"]


async def _verificar(http: AsyncClient, token: str, codigo: str):  # noqa: ANN202
    return await http.post(f"{API}/auth/2fa/verificar", json={"token_temporario": token, "codigo": codigo})


async def test_token_parcial_nao_acessa_a_api(http: AsyncClient, usuario_2fa, sessao: AsyncSession):
    usuario, _ = usuario_2fa
    # versao_sessao == 0 era o cenário em que o token parcial (sem "sv") passava como acesso
    assert usuario.versao_sessao == 0
    token = await _login_parcial(http, usuario)
    r = await http.get(f"{API}/auth/eu", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


async def test_codigo_totp_correto_conclui_o_login(http: AsyncClient, usuario_2fa):
    usuario, segredo = usuario_2fa
    token = await _login_parcial(http, usuario)
    r = await _verificar(http, token, pyotp.TOTP(segredo).now())
    assert r.status_code == 200
    acesso = r.json()["access_token"]
    assert (await http.get(f"{API}/auth/eu", headers={"Authorization": f"Bearer {acesso}"})).status_code == 200


async def test_token_parcial_e_de_uso_unico(http: AsyncClient, usuario_2fa):
    usuario, segredo = usuario_2fa
    token = await _login_parcial(http, usuario)
    codigo = pyotp.TOTP(segredo).now()
    assert (await _verificar(http, token, codigo)).status_code == 200
    assert (await _verificar(http, token, codigo)).status_code == 401


async def test_quinto_erro_invalida_o_token_mesmo_com_codigo_correto(http: AsyncClient, usuario_2fa):
    usuario, segredo = usuario_2fa
    token = await _login_parcial(http, usuario)
    for _ in range(4):
        r = await _verificar(http, token, "000000")
        assert r.status_code == 400 and r.json()["erro"]["codigo"] == "codigo_invalido"
    r = await _verificar(http, token, "000000")
    assert r.status_code == 401
    # código correto já não adianta: é preciso novo login com senha
    assert (await _verificar(http, token, pyotp.TOTP(segredo).now())).status_code == 401
    novo = await _login_parcial(http, usuario)
    assert (await _verificar(http, novo, pyotp.TOTP(segredo).now())).status_code == 200


async def test_token_parcial_sem_jti_e_rejeitado(http: AsyncClient, usuario_2fa):
    import jwt as _jwt

    from app.config import get_settings
    from app.security import ALGORITMO

    usuario, segredo = usuario_2fa
    sem_jti = _jwt.encode({"sub": str(usuario.id), "requer_2fa": True}, get_settings().secret_key, algorithm=ALGORITMO)
    assert (await _verificar(http, sem_jti, pyotp.TOTP(segredo).now())).status_code == 401


async def test_token_de_acesso_nao_serve_como_token_parcial(http: AsyncClient, usuario_2fa):
    usuario, segredo = usuario_2fa
    acesso = criar_token(usuario.id, usuario.versao_sessao)
    assert (await _verificar(http, acesso, pyotp.TOTP(segredo).now())).status_code == 401


async def test_limite_por_usuario_responde_429(http: AsyncClient, usuario_2fa):
    usuario, segredo = usuario_2fa
    # cada login parcial novo zera o contador por jti, mas não o limite por usuário
    for _ in range(2):
        token = await _login_parcial(http, usuario)
        for _ in range(4):
            assert (await _verificar(http, token, "000000")).status_code == 400
        assert (await _verificar(http, token, "000000")).status_code == 401
    token = await _login_parcial(http, usuario)
    for _ in range(2):
        assert (await _verificar(http, token, "000000")).status_code == 400
    r = await _verificar(http, token, pyotp.TOTP(segredo).now())
    assert r.status_code == 429 and r.json()["erro"]["codigo"] == "muitas_tentativas"
    limitador_de_2fa._falhas.clear()
    assert (await _verificar(http, token, pyotp.TOTP(segredo).now())).status_code == 200


async def test_backup_code_funciona_uma_vez_e_falha_conta_como_erro(http: AsyncClient, usuario_2fa):
    usuario, _ = usuario_2fa
    token = await _login_parcial(http, usuario)
    assert (await _verificar(http, token, "ffffffffffff")).status_code == 400  # backup errado conta como erro
    assert controle_token_parcial._erros  # contabilizado
    assert (await _verificar(http, token, CODIGO_BACKUP)).status_code == 200

    outro = await _login_parcial(http, usuario)
    r = await _verificar(http, outro, CODIGO_BACKUP)  # já usado
    assert r.status_code == 400 and r.json()["erro"]["codigo"] == "codigo_invalido"

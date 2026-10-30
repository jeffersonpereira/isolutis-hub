"""Cadastro completo da empresa ativa, logomarca e paleta de cores. Exige o banco de testes (ver conftest)."""

import base64

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.render import orcamento_pdf
from app.documents.reportlab_base import Identidade
from app.models import Empresa, Municipio, Usuario, UsuarioEmpresa
from app.security import gerar_hash
from app.services.empresa import LOGO_MAX_BYTES, decodificar_logo
from tests.conftest import SENHA

API = "/api/v1"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 32


def _data_url(dados: bytes, tipo: str = "image/png") -> str:
    return f"data:{tipo};base64,{base64.b64encode(dados).decode()}"


async def _cabecalhos(http: AsyncClient, sessao: AsyncSession, empresa: Empresa, papel: str) -> dict[str, str]:
    email = f"{papel}@empresa.com"
    u = Usuario(email=email, nome=papel.title(), senha_hash=gerar_hash(SENHA))
    sessao.add(u)
    await sessao.flush()
    sessao.add(UsuarioEmpresa(empresa_id=empresa.id, usuario_id=u.id, papel=papel, ativo=True))
    await sessao.commit()
    r = await http.post(f"{API}/auth/login", json={"email": email, "senha": SENHA})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}", "X-Empresa-ID": str(empresa.id)}


@pytest.fixture
async def empresa(sessao: AsyncSession) -> Empresa:
    e = Empresa(nome="Alfa")
    sessao.add(e)
    await sessao.commit()
    return e


@pytest.fixture
async def admin_h(http: AsyncClient, sessao: AsyncSession, empresa: Empresa) -> dict[str, str]:
    return await _cabecalhos(http, sessao, empresa, "admin")


@pytest.fixture
async def membro_h(http: AsyncClient, sessao: AsyncSession, empresa: Empresa) -> dict[str, str]:
    return await _cabecalhos(http, sessao, empresa, "membro")


CADASTRO = {
    "nome": "Alfa",
    "tipo_inscricao": "CNPJ",
    "inscricao": "11.222.333/0001-81",
    "razao_social": "Alfa Tecnologia Ltda",
    "nome_fantasia": "Alfa Tech",
    "inscricao_estadual": "123456",
    "regime_tributario": "simples_nacional",
    "data_abertura": "2020-01-15",
    "email": "contato@alfa.com.br",
    "telefone": "(71) 99999-0000",
    "cep": "40000-000",
    "logradouro": "Rua A",
    "numero": "10",
    "bairro": "Centro",
}


async def test_qualquer_papel_le_e_so_admin_altera(http: AsyncClient, admin_h: dict, membro_h: dict):
    r = await http.get(f"{API}/empresas/ativa", headers=membro_h)
    assert r.status_code == 200, r.text
    assert r.json()["nome"] == "Alfa" and r.json()["logo"] is None and r.json()["paleta"] is None
    for metodo, caminho, corpo in [
        ("PUT", "/empresas/ativa", CADASTRO),
        ("PUT", "/empresas/ativa/logo", {"imagem": _data_url(PNG)}),
        ("DELETE", "/empresas/ativa/logo", None),
        ("PUT", "/empresas/ativa/paleta", {"primaria": "#112233", "destaque": "#445566"}),
        ("DELETE", "/empresas/ativa/paleta", None),
    ]:
        r = await http.request(metodo, f"{API}{caminho}", json=corpo, headers=membro_h)
        assert r.status_code == 403, f"{metodo} {caminho}: {r.text}"


async def test_cadastro_completo_normaliza_e_devolve_uf(http: AsyncClient, sessao: AsyncSession, admin_h: dict):
    municipio = Municipio(nome="Salvador", uf="BA")
    sessao.add(municipio)
    await sessao.commit()
    r = await http.put(f"{API}/empresas/ativa", json={**CADASTRO, "municipio_id": str(municipio.id)}, headers=admin_h)
    assert r.status_code == 200, r.text
    corpo = r.json()
    assert corpo["inscricao"] == "11222333000181"
    assert corpo["cep"] == "40000000"
    assert corpo["uf"] == "BA"
    assert corpo["razao_social"] == "Alfa Tecnologia Ltda"
    # Campos vazios viram nulos; sem inscrição, o tipo também é limpo
    r = await http.put(
        f"{API}/empresas/ativa",
        json={"nome": "Alfa", "tipo_inscricao": "CNPJ", "inscricao": "", "email": ""},
        headers=admin_h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["inscricao"] is None and r.json()["tipo_inscricao"] is None and r.json()["email"] is None


@pytest.mark.parametrize(
    "alteracao",
    [
        {"inscricao": "11222333000180"},  # dígito verificador errado
        {"tipo_inscricao": "CPF", "inscricao": "11222333000181"},  # CNPJ declarado como CPF
        {"tipo_inscricao": None},  # número sem tipo
    ],
)
async def test_inscricao_invalida(http: AsyncClient, admin_h: dict, alteracao: dict):
    r = await http.put(f"{API}/empresas/ativa", json={**CADASTRO, **alteracao}, headers=admin_h)
    assert r.status_code == 422, r.text


async def test_inscricao_duplicada_entre_empresas(http: AsyncClient, sessao: AsyncSession, admin_h: dict):
    outra = Empresa(nome="Beta", tipo_inscricao="CNPJ", inscricao="11222333000181")
    sessao.add(outra)
    await sessao.commit()
    r = await http.put(f"{API}/empresas/ativa", json=CADASTRO, headers=admin_h)
    assert r.status_code == 422
    assert "inscrição" in r.json()["erro"]["mensagem"]


async def test_logo_envio_leitura_e_remocao(http: AsyncClient, admin_h: dict, membro_h: dict):
    r = await http.put(f"{API}/empresas/ativa/logo", json={"imagem": _data_url(PNG)}, headers=admin_h)
    assert r.status_code == 200, r.text
    assert r.json()["logo"] == _data_url(PNG)
    lida = (await http.get(f"{API}/empresas/ativa", headers=membro_h)).json()
    assert lida["logo"] == _data_url(PNG)
    assert (await http.delete(f"{API}/empresas/ativa/logo", headers=admin_h)).status_code == 204
    assert (await http.get(f"{API}/empresas/ativa", headers=membro_h)).json()["logo"] is None


def test_logo_detecta_o_tipo_pelos_bytes():
    assert decodificar_logo(_data_url(JPEG, "image/png")) == (JPEG, "image/jpeg")
    assert decodificar_logo(base64.b64encode(WEBP).decode()) == (WEBP, "image/webp")


@pytest.mark.parametrize(
    "imagem",
    [
        _data_url(b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", "image/svg+xml"),
        _data_url(b"GIF89a" + b"\x00" * 10, "image/gif"),
        "data:image/png;base64,isto-nao-e-base64!",
        _data_url(PNG + b"\x00" * LOGO_MAX_BYTES),
    ],
)
async def test_logo_recusada(http: AsyncClient, admin_h: dict, imagem: str):
    r = await http.put(f"{API}/empresas/ativa/logo", json={"imagem": imagem}, headers=admin_h)
    assert r.status_code == 422, r.text


async def test_paleta_definir_validar_e_restaurar(http: AsyncClient, admin_h: dict, membro_h: dict):
    r = await http.put(
        f"{API}/empresas/ativa/paleta", json={"primaria": "#1A2B3C", "destaque": "#00aa88"}, headers=admin_h
    )
    assert r.status_code == 200, r.text
    assert r.json()["paleta"] == {"primaria": "#1a2b3c", "destaque": "#00aa88"}
    assert (await http.get(f"{API}/empresas/ativa", headers=membro_h)).json()["paleta"]["primaria"] == "#1a2b3c"
    for invalida in ({"primaria": "red", "destaque": "#00aa88"}, {"primaria": "#123", "destaque": "#00aa88"}):
        assert (await http.put(f"{API}/empresas/ativa/paleta", json=invalida, headers=admin_h)).status_code == 422
    r = await http.delete(f"{API}/empresas/ativa/paleta", headers=admin_h)
    assert r.status_code == 200 and r.json()["paleta"] is None


async def test_paleta_e_logo_isoladas_por_empresa(http: AsyncClient, sessao: AsyncSession, admin_h: dict):
    beta = Empresa(nome="Beta")
    sessao.add(beta)
    await sessao.commit()
    await http.put(f"{API}/empresas/ativa/paleta", json={"primaria": "#111111", "destaque": "#222222"}, headers=admin_h)
    beta_h = await _cabecalhos(http, sessao, beta, "comercial")
    corpo = (await http.get(f"{API}/empresas/ativa", headers=beta_h)).json()
    assert corpo["nome"] == "Beta" and corpo["paleta"] is None


def test_documento_usa_a_identidade_da_empresa():
    """Nome da empresa com `<`/`&` (caracteres de marcação do ReportLab) não pode quebrar a geração do PDF."""
    import io
    from datetime import date
    from decimal import Decimal
    from types import SimpleNamespace

    import PIL.Image

    png_valido = io.BytesIO()
    PIL.Image.new("RGB", (4, 4), "white").save(png_valido, format="PNG")

    orc = SimpleNamespace(
        numero="2026-001", data=date(2026, 1, 1), valido_ate=date(2026, 1, 31), itens=[], desconto=Decimal(0),
        total_projeto=Decimal(0), total_mensal=Decimal(0), obs=None,
    )  # fmt: skip
    cliente = SimpleNamespace(nome="Cliente", contato=None, cargo=None, cpf_cnpj=None, tipo_pessoa="PJ")
    emissor = Identidade(
        nome="Alfa <Tech> & Cia", documento="CNPJ 11.222.333/0001-81", logo=_data_url(png_valido.getvalue())
    )

    pdf = orcamento_pdf(orc, cliente, emissor)  # type: ignore[arg-type]
    assert pdf.startswith(b"%PDF")

"""Matriz de papéis e garantia estrutural de que nenhuma rota de dados fica sem checagem de permissão.

Não usa banco: só inspeciona o app e os schemas (por isso sobrepõe a fixture de sessão que migra o banco).
"""

import pytest
from fastapi.routing import APIRoute
from pydantic import ValidationError

from app.domain.papeis import PAPEIS, PERMISSOES, PERMISSOES_POR_PAPEL, ordenadas, permissoes_do_papel
from app.main import criar_app
from app.schemas.convite import ConviteEntrada
from app.schemas.usuario import UsuarioAtualizar, UsuarioCriar


@pytest.fixture(scope="session", autouse=True)
def banco_migrado() -> None:
    """Sem banco neste módulo."""


# Rotas sem `exige(...)` por desenho: públicas, ou que só pedem login porque ainda não há empresa ativa.
PUBLICAS_OU_SEM_EMPRESA: set[tuple[str, str]] = {
    ("POST", "/auth/login"),
    ("GET", "/auth/convite/{token}"),
    ("POST", "/auth/convite/{token}/aceitar"),
    ("POST", "/auth/2fa/verificar"),
    ("GET", "/auth/eu"),
    ("POST", "/auth/trocar-senha"),
    ("POST", "/auth/2fa/setup"),
    ("POST", "/auth/2fa/confirmar"),
    ("DELETE", "/auth/2fa"),
    ("GET", "/empresas"),  # lista as empresas para a escolha da empresa ativa: ainda não há X-Empresa-ID
}
PREFIXO = "/api/v1"


def _permissoes_da_rota(rota: APIRoute) -> set[str]:
    achadas: set[str] = set()

    def percorrer(dependente) -> None:  # noqa: ANN001
        permissao = getattr(dependente.call, "permissao_exigida", None)
        if permissao:
            achadas.add(permissao)
        for filha in dependente.dependencies:
            percorrer(filha)

    percorrer(rota.dependant)
    return achadas


def test_toda_rota_de_dados_exige_permissao():
    app = criar_app()
    sem_checagem = []
    for rota in app.routes:
        if not isinstance(rota, APIRoute) or not rota.path.startswith(PREFIXO):
            continue
        caminho = rota.path.removeprefix(PREFIXO)
        for metodo in sorted(rota.methods - {"HEAD", "OPTIONS"}):
            if (metodo, caminho) in PUBLICAS_OU_SEM_EMPRESA:
                continue
            if not _permissoes_da_rota(rota):
                sem_checagem.append(f"{metodo} {caminho}")
    assert not sem_checagem, "Rotas sem permissão declarada (use exige(...) ou liste como pública): " + ", ".join(
        sem_checagem
    )


def test_lista_de_excecoes_so_tem_rotas_que_existem():
    app = criar_app()
    existentes = {
        (metodo, rota.path.removeprefix(PREFIXO))
        for rota in app.routes
        if isinstance(rota, APIRoute) and rota.path.startswith(PREFIXO)
        for metodo in rota.methods
    }
    assert existentes >= PUBLICAS_OU_SEM_EMPRESA


@pytest.mark.parametrize(
    ("metodo", "caminho", "permissao"),
    [
        ("GET", "/clientes", "comercial"),
        ("GET", "/clientes/referencias", "base"),
        ("GET", "/negocios", "comercial"),
        ("GET", "/orcamentos", "comercial"),
        ("GET", "/produtos", "comercial"),
        ("GET", "/faturamento", "financeiro"),
        ("GET", "/despesas", "financeiro"),
        ("GET", "/relatorios/dre", "financeiro"),
        ("GET", "/financeiro/titulos", "financeiro"),
        ("GET", "/financeiro/instituicoes", "base"),
        ("GET", "/parceiros", "financeiro"),
        ("GET", "/parceiros/papeis", "base"),
        ("GET", "/painel", "base"),
        ("GET", "/projetos", "base"),
        ("GET", "/tarefas", "base"),
        ("GET", "/equipe", "base"),
        ("GET", "/usuarios", "administracao"),
        ("GET", "/convites", "administracao"),
        ("PATCH", "/empresas/ativa", "administracao"),
        ("GET", "/onboarding/status", "base"),
        ("POST", "/onboarding/concluir", "administracao"),
    ],
)
def test_rotas_representativas_exigem_a_permissao_da_matriz(metodo: str, caminho: str, permissao: str):
    app = criar_app()
    rota = next(
        r for r in app.routes if isinstance(r, APIRoute) and r.path == PREFIXO + caminho and metodo in r.methods
    )
    assert _permissoes_da_rota(rota) == {permissao}


def test_nao_existe_rota_para_criar_empresa():
    app = criar_app()
    metodos = {m for r in app.routes if isinstance(r, APIRoute) and r.path == f"{PREFIXO}/empresas" for m in r.methods}
    assert "POST" not in metodos


# ----------------------------------------------------------------------------- matriz de papéis
def test_matriz_de_permissoes():
    assert set(PERMISSOES_POR_PAPEL) == set(PAPEIS) == {"admin", "financeiro", "comercial", "membro"}
    assert permissoes_do_papel("admin") == set(PERMISSOES)
    assert permissoes_do_papel("financeiro") == {"base", "financeiro"}
    assert permissoes_do_papel("comercial") == {"base", "comercial"}
    assert permissoes_do_papel("membro") == {"base"}


@pytest.mark.parametrize("papel", [None, "", "superusuario"])
def test_papel_desconhecido_nao_concede_nada(papel: str | None):
    assert permissoes_do_papel(papel) == frozenset()


def test_permissoes_saem_em_ordem_estavel():
    assert ordenadas(permissoes_do_papel("admin")) == ["base", "comercial", "financeiro", "administracao"]


# ----------------------------------------------------------------------------- schemas
@pytest.mark.parametrize("papel", ["admin", "financeiro", "comercial", "membro"])
def test_convite_aceita_os_quatro_papeis(papel: str):
    assert ConviteEntrada(nome="Bia", email="bia@exemplo.com", papel=papel).papel == papel


@pytest.mark.parametrize("papel", ["root", "", "Admin"])
def test_papel_invalido_e_recusado(papel: str):
    with pytest.raises(ValidationError):
        ConviteEntrada(nome="Bia", email="bia@exemplo.com", papel=papel)
    with pytest.raises(ValidationError):
        UsuarioCriar(nome="Bia", email="bia@exemplo.com", senha="senha-longa-1", papel=papel)
    with pytest.raises(ValidationError):
        UsuarioAtualizar(nome="Bia", papel=papel, versao=1)


def test_usuario_novo_nasce_com_acesso_basico():
    assert UsuarioCriar(nome="Bia", email="bia@exemplo.com", senha="senha-longa-1").papel == "membro"

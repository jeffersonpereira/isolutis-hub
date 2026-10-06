from fastapi import APIRouter, Request, Response

from app.deps import Sessao, UsuarioLogado
from app.errors import NaoAutenticado, RegraDeNegocio
from app.ratelimit import limitador_de_login
from app.schemas.convite import AceitarConviteEntrada, ConviteInfo
from app.schemas.usuario import LoginEntrada, TokenSaida, TrocarSenhaEntrada, UsuarioLeitura
from app.security import criar_token
from app.services import convites as svc_convites
from app.services import usuarios as svc

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenSaida)
async def login(dados: LoginEntrada, sessao: Sessao, request: Request) -> TokenSaida:
    chave = f"{str(dados.email).lower()}|{request.client.host if request.client else '-'}"
    limitador_de_login.verificar(chave)
    try:
        usuario = await svc.autenticar(sessao, str(dados.email), dados.senha)
    except NaoAutenticado:
        limitador_de_login.registrar_falha(chave)
        raise
    limitador_de_login.zerar(chave)
    # Forçar carregamento de atributos lazy-loaded antes de sair da sessão
    await sessao.refresh(usuario, ["senha_definida"])
    return TokenSaida(
        access_token=criar_token(usuario.id, usuario.versao_sessao), usuario=UsuarioLeitura.model_validate(usuario)
    )


@router.get("/eu", response_model=UsuarioLeitura)
async def eu(usuario: UsuarioLogado) -> UsuarioLeitura:
    return UsuarioLeitura.model_validate(usuario)


@router.post("/trocar-senha", status_code=204)
async def trocar_senha(dados: TrocarSenhaEntrada, usuario: UsuarioLogado, sessao: Sessao) -> Response:
    await svc.trocar_senha(sessao, usuario, dados.senha_atual, dados.nova_senha)
    return Response(status_code=204)


@router.get("/convite/{token}", response_model=ConviteInfo, tags=["Convites"])
async def verificar_convite(token: str, sessao: Sessao) -> ConviteInfo:
    """Retorna informações públicas do convite para exibir na tela de aceitação."""
    info = await svc_convites.verificar_convite_publico(sessao, token)
    return ConviteInfo.model_validate(info)


@router.post("/convite/{token}/aceitar", response_model=TokenSaida, tags=["Convites"])
async def aceitar_convite(token: str, dados: AceitarConviteEntrada, sessao: Sessao) -> TokenSaida:
    """Aceita o convite e cria (ou ativa) o usuário com a senha informada."""
    if dados.senha != dados.confirmar_senha:
        raise RegraDeNegocio("As senhas não conferem.")
    usuario = await svc_convites.aceitar_convite(sessao, token, dados.senha)
    await sessao.refresh(usuario, ["senha_definida"])
    return TokenSaida(
        access_token=criar_token(usuario.id, usuario.versao_sessao),
        usuario=UsuarioLeitura.model_validate(usuario),
    )

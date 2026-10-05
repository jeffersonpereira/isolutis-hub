from fastapi import APIRouter, Request, Response

from app.deps import Sessao, UsuarioLogado
from app.errors import NaoAutenticado
from app.ratelimit import limitador_de_login
from app.schemas.usuario import LoginEntrada, TokenSaida, TrocarSenhaEntrada, UsuarioLeitura
from app.security import criar_token
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

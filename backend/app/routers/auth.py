import uuid
from datetime import UTC, datetime, timedelta

import jwt as _jwt
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.deps import Sessao, UsuarioLogado
from app.errors import NaoAutenticado, RegraDeNegocio
from app.ratelimit import limitador_de_login
from app.schemas.convite import AceitarConviteEntrada, ConviteInfo
from app.schemas.usuario import LoginEntrada, TokenSaida, TrocarSenhaEntrada, UsuarioLeitura
from app.security import ALGORITMO, criar_token
from app.services import convites as svc_convites
from app.services import usuarios as svc

router = APIRouter(prefix="/auth", tags=["Autenticação"])

_MINUTOS_TOKEN_PARCIAL = 5


def _criar_token_parcial(usuario_id: object) -> str:
    """Emite um JWT de curta duração com claim requer_2fa=True.

    Esse token não concede acesso à API; serve apenas para identificar o
    usuário no endpoint POST /auth/2fa/verificar.
    """
    cfg = get_settings()
    agora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "requer_2fa": True,
        "jti": uuid.uuid4().hex,
        "iat": agora,
        "exp": agora + timedelta(minutes=_MINUTOS_TOKEN_PARCIAL),
    }
    return _jwt.encode(payload, cfg.secret_key, algorithm=ALGORITMO)


@router.post("/login", response_model=TokenSaida)
async def login(dados: LoginEntrada, sessao: Sessao, request: Request) -> TokenSaida | JSONResponse:
    chave = f"{str(dados.email).lower()}|{request.client.host if request.client else '-'}"
    limitador_de_login.verificar(chave)
    try:
        usuario = await svc.autenticar(sessao, str(dados.email), dados.senha)
    except NaoAutenticado:
        limitador_de_login.registrar_falha(chave)
        raise
    limitador_de_login.zerar(chave)

    # Se o usuário tiver 2FA ativo, emitir token parcial em vez do JWT completo
    if usuario.totp_ativo:
        token_parcial = _criar_token_parcial(usuario.id)
        return JSONResponse(
            status_code=200,
            content={"requer_2fa": True, "token_temporario": token_parcial},
        )

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

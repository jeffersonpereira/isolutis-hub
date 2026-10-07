"""Senhas (Argon2id) e tokens de acesso (JWT HS256)."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import get_settings

_hasher = PasswordHasher()
ALGORITMO = "HS256"
TAMANHO_MINIMO_SENHA = 8


def gerar_hash(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, hash_: str) -> bool:
    try:
        return _hasher.verify(hash_, senha)
    except (VerificationError, InvalidHashError):
        return False


def precisa_rehash(hash_: str) -> bool:
    return _hasher.check_needs_rehash(hash_)


def criar_token(usuario_id: UUID, versao_sessao: int = 0) -> str:
    cfg = get_settings()
    agora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "sv": versao_sessao,
        "iat": agora,
        "exp": agora + timedelta(minutes=cfg.token_minutos),
    }
    return jwt.encode(payload, cfg.secret_key, algorithm=ALGORITMO)


def ler_token(token: str) -> tuple[UUID, int] | None:
    """Devolve (id, versão da sessão), ou None se inválido/expirado."""
    try:
        dados = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITMO])
        if dados.get("requer_2fa"):
            return None  # token parcial do 2FA nunca vale como token de acesso
        versao = dados.get("sv", 0)  # tokens anteriores à versão de sessão continuam válidos até expirarem
        if not isinstance(versao, int) or versao < 0:
            return None
        return UUID(dados["sub"]), versao
    except (jwt.PyJWTError, KeyError, ValueError):
        return None

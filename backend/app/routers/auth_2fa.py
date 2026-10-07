"""Endpoints de autenticação em dois fatores (TOTP).

Fluxo geral:
  1. POST /auth/2fa/setup      — gera segredo e QR code (usuário já autenticado)
  2. POST /auth/2fa/confirmar  — verifica primeiro código, ativa 2FA e invalida sessões antigas
  3. POST /auth/2fa/verificar  — endpoint público: troca token temporário por JWT completo
  4. DELETE /auth/2fa          — desativa 2FA após confirmar código atual
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import jwt as _jwt
import pyotp
from fastapi import APIRouter, Query
from pydantic import Field
from sqlalchemy import Integer, delete, select
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.config import get_settings
from app.deps import Sessao, UsuarioLogado
from app.errors import ErroApp, NaoAutenticado
from app.models import Usuario
from app.models.base import Base
from app.schemas.comum import Entrada, Leitura
from app.schemas.usuario import TokenSaida, UsuarioLeitura
from app.security import ALGORITMO, criar_token, gerar_hash, ler_token, verificar_senha
from app.services.totp import (
    criptografar_segredo,
    descriptografar_segredo,
    gerar_backup_codes,
    gerar_qr_code,
    gerar_segredo,
    verificar_codigo,
)

router = APIRouter(prefix="/auth/2fa", tags=["Autenticação"])


# ---------------------------------------------------------------------------
# Modelo SQLAlchemy para backup codes — criado pela migração 0007
# ---------------------------------------------------------------------------

class TotpBackupCode(Base):
    """Backup codes de recuperação de 2FA (hashes Argon2id)."""

    __tablename__ = "totp_backup_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    codigo_hash: Mapped[str] = mapped_column(nullable=False)
    usado_em: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SetupTotpSaida(Leitura):
    qr_code: str
    provisioning_uri: str
    backup_codes: list[str]


class ConfirmarTotpEntrada(Entrada):
    codigo: str = Field(min_length=6, max_length=6)
    backup_codes: list[str] = Field(min_length=8, max_length=8)


class VerificarTotpEntrada(Entrada):
    token_temporario: str
    # Aceita código TOTP de 6 dígitos ou backup code de 12 hex chars
    codigo: str = Field(min_length=6, max_length=12)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/setup", response_model=SetupTotpSaida)
async def setup_2fa(usuario: UsuarioLogado, sessao: Sessao) -> SetupTotpSaida:
    """Inicia o setup do 2FA: gera segredo, QR code e backup codes provisórios.

    O 2FA só fica ativo após confirmar um código em /auth/2fa/confirmar.
    """
    segredo = gerar_segredo()
    usuario.totp_secret = criptografar_segredo(segredo)
    await sessao.commit()

    backup_codes = gerar_backup_codes(8)
    qr = gerar_qr_code(segredo, usuario.email)
    uri = pyotp.TOTP(segredo).provisioning_uri(name=usuario.email, issuer_name="iSolutis Hub")

    return SetupTotpSaida(qr_code=qr, provisioning_uri=uri, backup_codes=backup_codes)


@router.post("/confirmar", response_model=TokenSaida)
async def confirmar_2fa(
    dados: ConfirmarTotpEntrada,
    usuario: UsuarioLogado,
    sessao: Sessao,
) -> TokenSaida:
    """Confirma o primeiro código TOTP e ativa 2FA.

    Invalida todas as sessões existentes (incrementa versao_sessao) e emite
    um novo JWT completo para a sessão atual continuar sem re-login.
    """
    if not usuario.totp_secret:
        raise ErroApp("Configure o 2FA primeiro em /auth/2fa/setup.", codigo="2fa_nao_configurado")

    segredo = descriptografar_segredo(usuario.totp_secret)
    if not verificar_codigo(segredo, dados.codigo):
        raise ErroApp("Código inválido. Verifique o horário do seu dispositivo.", codigo="codigo_invalido")

    usuario.totp_ativo = True
    usuario.versao_sessao += 1

    await sessao.execute(delete(TotpBackupCode).where(TotpBackupCode.usuario_id == usuario.id))
    for code in dados.backup_codes:
        sessao.add(TotpBackupCode(usuario_id=usuario.id, codigo_hash=gerar_hash(code)))

    await sessao.commit()
    await sessao.refresh(usuario)

    return TokenSaida(
        access_token=criar_token(usuario.id, usuario.versao_sessao),
        usuario=UsuarioLeitura.model_validate(usuario),
    )


@router.post("/verificar", response_model=TokenSaida)
async def verificar_2fa(dados: VerificarTotpEntrada, sessao: Sessao) -> TokenSaida:
    """Endpoint público: valida código TOTP ou backup code após login parcial e emite JWT completo."""
    # 1. Decodificar token temporário
    identidade = ler_token(dados.token_temporario)
    if identidade is None:
        raise NaoAutenticado("Token temporário inválido ou expirado.")

    usuario_id, _ = identidade

    # 2. Verificar claim requer_2fa no payload
    try:
        payload = _jwt.decode(
            dados.token_temporario,
            get_settings().secret_key,
            algorithms=[ALGORITMO],
        )
    except _jwt.PyJWTError:
        raise NaoAutenticado("Token temporário inválido ou expirado.")

    if not payload.get("requer_2fa"):
        raise NaoAutenticado("Token não é de autenticação parcial.")

    # 3. Buscar usuário
    usuario = await sessao.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        raise NaoAutenticado("Usuário não encontrado ou inativo.")

    if not usuario.totp_ativo or not usuario.totp_secret:
        raise NaoAutenticado("2FA não está ativo para este usuário.")

    segredo = descriptografar_segredo(usuario.totp_secret)

    # 4a. Código TOTP normal
    if verificar_codigo(segredo, dados.codigo):
        await sessao.refresh(usuario)
        return TokenSaida(
            access_token=criar_token(usuario.id, usuario.versao_sessao),
            usuario=UsuarioLeitura.model_validate(usuario),
        )

    # 4b. Backup code
    resultado = await sessao.execute(
        select(TotpBackupCode).where(
            TotpBackupCode.usuario_id == usuario.id,
            TotpBackupCode.usado_em.is_(None),
        )
    )
    for backup in resultado.scalars().all():
        if verificar_senha(dados.codigo, backup.codigo_hash):
            backup.usado_em = datetime.now(UTC)
            await sessao.commit()
            await sessao.refresh(usuario)
            return TokenSaida(
                access_token=criar_token(usuario.id, usuario.versao_sessao),
                usuario=UsuarioLeitura.model_validate(usuario),
            )

    raise ErroApp(
        "Código inválido. Verifique o horário do seu dispositivo ou use um backup code.",
        codigo="codigo_invalido",
    )


@router.delete("", response_model=None, status_code=204)
async def desativar_2fa(
    usuario: UsuarioLogado,
    sessao: Sessao,
    codigo: str = Query(min_length=6, max_length=6),
) -> None:
    """Desativa 2FA após confirmar o código TOTP atual."""
    if not usuario.totp_ativo or not usuario.totp_secret:
        raise ErroApp("O 2FA não está ativo.", codigo="2fa_nao_ativo")

    segredo = descriptografar_segredo(usuario.totp_secret)
    if not verificar_codigo(segredo, codigo):
        raise ErroApp("Código inválido. Verifique o horário do seu dispositivo.", codigo="codigo_invalido")

    usuario.totp_ativo = False
    usuario.totp_secret = None
    await sessao.execute(delete(TotpBackupCode).where(TotpBackupCode.usuario_id == usuario.id))
    await sessao.commit()

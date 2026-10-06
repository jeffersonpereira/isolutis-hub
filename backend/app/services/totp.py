"""Utilitários TOTP: gerar segredo, QR code, verificação e backup codes."""

import base64
import io
import secrets

import pyotp
import qrcode
from cryptography.fernet import Fernet

from app.config import get_settings


def _fernet() -> Fernet:
    """Fernet baseado nos primeiros 32 bytes da secret_key (URL-safe base64)."""
    raw = get_settings().secret_key.encode()[:32].ljust(32, b"0")
    key = base64.urlsafe_b64encode(raw)
    return Fernet(key)


def gerar_segredo() -> str:
    return pyotp.random_base32()


def criptografar_segredo(segredo: str) -> str:
    return _fernet().encrypt(segredo.encode()).decode()


def descriptografar_segredo(segredo_cifrado: str) -> str:
    return _fernet().decrypt(segredo_cifrado.encode()).decode()


def gerar_qr_code(segredo: str, email: str, empresa: str = "iSolutis Hub") -> str:
    """Retorna o QR code como data URI PNG base64."""
    uri = pyotp.TOTP(segredo).provisioning_uri(name=email, issuer_name=empresa)
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def verificar_codigo(segredo: str, codigo: str, janela: int = 1) -> bool:
    return pyotp.TOTP(segredo).verify(codigo, valid_window=janela)


def gerar_backup_codes(n: int = 8) -> list[str]:
    return [secrets.token_hex(6).upper() for _ in range(n)]

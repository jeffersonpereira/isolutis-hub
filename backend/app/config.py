"""Configuração por variáveis de ambiente (12-factor). Nada sensível fica no repositório."""

import json
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_CHAVE_DE_DESENVOLVIMENTO = "troque-esta-chave-em-producao"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HUB_", extra="ignore")

    ambiente: str = Field("desenvolvimento", description="desenvolvimento | producao | teste")
    database_url: str = "postgresql+psycopg://hub:hub@localhost:5432/hub_dev"
    migration_database_url: str | None = None
    secret_key: str = _CHAVE_DE_DESENVOLVIMENTO
    token_minutos: int = 60 * 12
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    # Pasta do build do frontend; quando existe, a API também serve o site (deploy em um único serviço).
    frontend_dist: str | None = None
    # Ajustes de log/SQL
    sql_echo: bool = False
    # SMTP para envio de e-mails de convite (env vars: HUB_SMTP_HOST, HUB_SMTP_PORT, etc.)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    base_url: str = "http://localhost:5173"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _separar_origens(cls, v: object) -> object:
        if isinstance(v, str):
            texto = v.strip()
            if texto.startswith("["):
                return json.loads(texto)
            return [origem.strip() for origem in texto.split(",") if origem.strip()]
        return v

    def validar_para_producao(self) -> None:
        import logging

        _logger = logging.getLogger(__name__)

        erros: list[str] = []
        if self.secret_key == _CHAVE_DE_DESENVOLVIMENTO or len(self.secret_key) < 32:
            erros.append("Defina HUB_SECRET_KEY com pelo menos 32 caracteres antes de subir em produção.")
        if self.ambiente == "producao" and erros:
            raise RuntimeError(" | ".join(erros))
        if not self.smtp_host:
            _logger.warning("HUB_SMTP_HOST não configurado — envio de e-mails desabilitado.")

        # Aviso: a verificação de admins sem 2FA exige acesso ao banco e deve ser
        # feita após o startup da aplicação (ver scheduler de notificações).
        _logger.warning(
            "Verificação de 2FA para admins deve ser feita após startup da aplicação"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

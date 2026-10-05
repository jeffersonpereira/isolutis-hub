"""Configuração por variáveis de ambiente (12-factor). Nada sensível fica no repositório."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_CHAVE_DE_DESENVOLVIMENTO = "troque-esta-chave-em-producao"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HUB_", extra="ignore")

    ambiente: str = Field("desenvolvimento", description="desenvolvimento | producao | teste")
    database_url: str = "postgresql+psycopg://hub:hub@localhost:5432/hub_dev"
    migration_database_url: str | None = None
    secret_key: str = _CHAVE_DE_DESENVOLVIMENTO
    token_minutos: int = 60 * 12
    cors_origins: list[str] = ["http://localhost:5173"]
    # Pasta do build do frontend; quando existe, a API também serve o site (deploy em um único serviço).
    frontend_dist: str | None = None
    # Ajustes de log/SQL
    sql_echo: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _separar_origens(cls, v: object) -> object:
        if isinstance(v, str) and not v.strip().startswith("["):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    def validar_para_producao(self) -> None:
        if self.ambiente == "producao" and (self.secret_key == _CHAVE_DE_DESENVOLVIMENTO or len(self.secret_key) < 32):
            raise RuntimeError("Defina HUB_SECRET_KEY com pelo menos 32 caracteres antes de subir em produção.")


@lru_cache
def get_settings() -> Settings:
    return Settings()

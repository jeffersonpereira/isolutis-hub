"""Contrato do cadastro único de parceiros (hub de papéis)."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AliasChoices, Field, model_validator

from app.financeiro.regras import so_digitos
from app.schemas.comum import Auditoria, Entrada, Leitura, TextoLongo, TextoOpcional

Origem = Literal["Site", "Indicação", "LinkedIn", "Instagram", "WhatsApp", "Evento", "Prospecção ativa", "Outro"]
Nome = Annotated[str, Field(min_length=1, max_length=150)]


class _CamposDoParceiro(Entrada):
    """Campos comuns às entradas do hub e da fachada de clientes; os valores são normalizados na validação."""

    cpf_cnpj: TextoOpcional = None
    nome: Nome
    segmento: TextoOpcional = None
    contato: TextoOpcional = None
    cargo: TextoOpcional = None
    telefone: TextoOpcional = None
    email: TextoOpcional = None
    origem: Origem | None = None
    obs: TextoLongo = None
    endereco: Annotated[str | None, Field(max_length=150)] = None
    cep: TextoOpcional = None
    municipio_id: UUID | None = None

    @model_validator(mode="after")
    def _normalizar(self) -> "_CamposDoParceiro":
        self.cpf_cnpj = so_digitos(self.cpf_cnpj) or None
        self.cep = so_digitos(self.cep) or None
        self.endereco = (self.endereco or "").strip() or None
        return self


class ParceiroEntrada(_CamposDoParceiro):
    tipo_pessoa: Literal["PJ", "PF"] = "PJ"
    papeis: Annotated[list[str], Field(min_length=1)]


class ParceiroAtualizar(ParceiroEntrada):
    versao: int = Field(ge=1)


class ParceiroLeitura(Auditoria):
    tipo_pessoa: str
    cpf_cnpj: str | None
    nome: str
    segmento: str | None
    contato: str | None
    cargo: str | None
    telefone: str | None
    email: str | None
    origem: str | None
    obs: str | None
    endereco: str | None
    cep: str | None
    municipio_id: UUID | None
    municipio_nome: str | None
    uf: str | None
    # Do ORM vem de `codigos_de_papel`; ao revalidar um dicionário (fachada de clientes) vem como `papeis`.
    papeis: list[str] = Field(validation_alias=AliasChoices("codigos_de_papel", "papeis"))


class PapelLeitura(Leitura):
    codigo: str
    nome: str

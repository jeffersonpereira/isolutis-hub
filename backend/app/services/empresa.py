"""Cadastro da empresa ativa e identidade visual (logomarca e paleta)."""

import base64
import binascii
import re
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.documents.render import formatar_documento
from app.documents.reportlab_base import Identidade
from app.errors import RegraDeNegocio
from app.financeiro.regras import cnpj_valido, cpf_valido
from app.models import Empresa, Municipio
from app.schemas.empresa import EmpresaDados, EmpresaLeitura, Paleta
from app.services.base import confirmar

LOGO_MAX_BYTES = 512 * 1024

# Assinaturas dos formatos aceitos. O tipo vem dos bytes, nunca do que o cliente declara; SVG fica de fora
# porque pode carregar script.
_ASSINATURAS: tuple[tuple[str, bytes, int], ...] = (
    ("image/png", b"\x89PNG\r\n\x1a\n", 0),
    ("image/jpeg", b"\xff\xd8\xff", 0),
    ("image/webp", b"WEBP", 8),
)


def logo_data_url(empresa: Empresa) -> str | None:
    if not empresa.logo or not empresa.logo_tipo:
        return None
    return f"data:{empresa.logo_tipo};base64,{base64.b64encode(empresa.logo).decode()}"


async def leitura(sessao: AsyncSession, empresa: Empresa) -> EmpresaLeitura:
    municipio = await sessao.get(Municipio, empresa.municipio_id) if empresa.municipio_id else None
    await sessao.refresh(empresa, ["logo"])
    return EmpresaLeitura(
        id=empresa.id, nome=empresa.nome, segmento=empresa.segmento,
        tipo_inscricao=empresa.tipo_inscricao, inscricao=empresa.inscricao, razao_social=empresa.razao_social,
        nome_fantasia=empresa.nome_fantasia, inscricao_estadual=empresa.inscricao_estadual,
        inscricao_municipal=empresa.inscricao_municipal, cnae_codigo=empresa.cnae_codigo,
        cnae_descricao=empresa.cnae_descricao, regime_tributario=empresa.regime_tributario,
        data_abertura=empresa.data_abertura, email=empresa.email, telefone=empresa.telefone, site=empresa.site,
        cep=empresa.cep, logradouro=empresa.logradouro, numero=empresa.numero, complemento=empresa.complemento,
        bairro=empresa.bairro, municipio_id=empresa.municipio_id, uf=municipio.uf if municipio else None,
        logo=logo_data_url(empresa), paleta=Paleta(**empresa.paleta) if empresa.paleta else None,
    )  # fmt: skip


def _validar_inscricao(dados: EmpresaDados) -> None:
    if dados.inscricao is None:
        return
    if dados.tipo_inscricao is None:
        raise RegraDeNegocio("Informe se a inscrição é CNPJ ou CPF.")
    valido = cnpj_valido(dados.inscricao) if dados.tipo_inscricao == "CNPJ" else cpf_valido(dados.inscricao)
    if not valido:
        raise RegraDeNegocio(f"{dados.tipo_inscricao} inválido. Confira os números digitados.")


async def atualizar(sessao: AsyncSession, empresa: Empresa, dados: EmpresaDados) -> EmpresaLeitura:
    _validar_inscricao(dados)
    if dados.municipio_id and await sessao.get(Municipio, dados.municipio_id) is None:
        raise RegraDeNegocio("Município não encontrado.")
    campos = dados.model_dump()
    if campos["inscricao"] is None:
        campos["tipo_inscricao"] = None
    for nome, valor in campos.items():
        setattr(empresa, nome, str(valor) if nome == "email" and valor is not None else valor)
    try:
        await confirmar(sessao)
    except IntegrityError as e:
        await sessao.rollback()
        raise RegraDeNegocio("Já existe outra empresa cadastrada com esta inscrição.") from e
    return await leitura(sessao, empresa)


def decodificar_logo(imagem: str) -> tuple[bytes, str]:
    """Aceita data URL ou base64 puro; devolve (bytes, tipo MIME detectado pelo conteúdo)."""
    conteudo = re.sub(r"^data:[^,]*,", "", imagem.strip(), count=1)
    try:
        dados = base64.b64decode(conteudo, validate=True)
    except (binascii.Error, ValueError) as e:
        raise RegraDeNegocio("Não foi possível ler a imagem enviada.") from e
    if not dados:
        raise RegraDeNegocio("A imagem enviada está vazia.")
    if len(dados) > LOGO_MAX_BYTES:
        raise RegraDeNegocio("A logomarca pode ter no máximo 512 KB.")
    for tipo, assinatura, deslocamento in _ASSINATURAS:
        if dados[deslocamento : deslocamento + len(assinatura)] == assinatura:
            if tipo == "image/webp" and not dados.startswith(b"RIFF"):
                continue
            return dados, tipo
    raise RegraDeNegocio("Formato não aceito. Envie a logomarca em PNG, JPEG ou WebP.")


async def definir_logo(sessao: AsyncSession, empresa: Empresa, imagem: str) -> EmpresaLeitura:
    empresa.logo, empresa.logo_tipo = decodificar_logo(imagem)
    empresa.logo_atualizada_em = datetime.now(UTC)
    await confirmar(sessao)
    return await leitura(sessao, empresa)


async def remover_logo(sessao: AsyncSession, empresa: Empresa) -> None:
    empresa.logo = None
    empresa.logo_tipo = None
    empresa.logo_atualizada_em = datetime.now(UTC)
    await confirmar(sessao)


async def definir_paleta(sessao: AsyncSession, empresa: Empresa, paleta: Paleta | None) -> EmpresaLeitura:
    empresa.paleta = paleta.model_dump() if paleta else None
    await confirmar(sessao)
    return await leitura(sessao, empresa)


async def identidade(sessao: AsyncSession, empresa: Empresa) -> Identidade:
    """Dados da empresa como aparecem nos documentos e relatórios (cabeçalho, rodapé e logomarca)."""
    await sessao.refresh(empresa, ["logo"])
    municipio = await sessao.get(Municipio, empresa.municipio_id) if empresa.municipio_id else None
    exibicao = empresa.nome_fantasia or empresa.nome
    rua = ", ".join(p for p in (empresa.logradouro, empresa.numero) if p)
    cidade = f"{municipio.nome}/{municipio.uf}" if municipio else None
    cep = f"CEP {empresa.cep[:5]}-{empresa.cep[5:]}" if empresa.cep else None
    endereco = " · ".join(p for p in (rua, empresa.complemento, empresa.bairro, cidade, cep) if p)
    return Identidade(
        nome=exibicao,
        subtitulo=empresa.razao_social if empresa.razao_social and empresa.razao_social != exibicao else None,
        documento=f"{empresa.tipo_inscricao} {formatar_documento(empresa.inscricao)}" if empresa.inscricao else None,
        contato=" · ".join(p for p in (empresa.telefone, empresa.email, empresa.site) if p) or None,
        endereco=endereco or None,
        logo=logo_data_url(empresa),
    )

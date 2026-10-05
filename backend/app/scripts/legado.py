"""Leitura e limpeza dos dados do sistema anterior (tabelas `hub_*` com coluna JSONB `dados`).

Funções puras (sem banco): cada `limpar_*` recebe o JSON antigo e devolve campos já compatíveis com o schema
estrito do novo banco, registrando no `Relatorio` tudo o que precisou ser ajustado ou descartado.
O mapeamento campo a campo está em docs/banco-de-dados.md (seção 9).
"""

import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Protocol

from app.financeiro.regras import documento_valido

COLECOES = (
    "hub_membros", "hub_clientes", "hub_produtos", "hub_negocios", "hub_orcamentos",
    "hub_faturamento", "hub_despesas", "hub_projetos", "hub_tarefas",
)  # fmt: skip

ORIGENS = {"Site", "Indicação", "LinkedIn", "Instagram", "WhatsApp", "Evento", "Prospecção ativa", "Outro"}
MOTIVOS = {"Preço", "Prazo", "Escolheu concorrente", "Adiou o projeto", "Sem resposta", "Fora do perfil"}
TIPOS_RECEITA = {"projeto", "mensal", "consultoria", "outro"}
FORMAS = {"Dinheiro (aporte)", "Equipamento", "Pagamento de despesa da empresa", "Outro"}


@dataclass
class LinhaLegada:
    id: str
    dados: dict[str, Any]
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None
    atualizado_por: str | None = None


class Origem(Protocol):
    def carregar(self, colecao: str) -> list[LinhaLegada]: ...


@dataclass
class Relatorio:
    importados: Counter = field(default_factory=Counter)
    ja_existiam: Counter = field(default_factory=Counter)
    avisos: list[str] = field(default_factory=list)

    def avisar(self, mensagem: str) -> None:
        self.avisos.append(mensagem)


# ----------------------------------------------------------------------------- origens
def _data_hora(v: Any) -> datetime | None:
    if isinstance(v, datetime):
        return v
    if isinstance(v, str) and v:
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _linha(registro: dict[str, Any]) -> LinhaLegada:
    dados = registro.get("dados") or {}
    if isinstance(dados, str):
        dados = json.loads(dados)
    return LinhaLegada(
        id=str(registro["id"]),
        dados=dados,
        criado_em=_data_hora(registro.get("criado_em")),
        atualizado_em=_data_hora(registro.get("atualizado_em")),
        atualizado_por=registro.get("atualizado_por"),
    )


class OrigemJson:
    """Pasta com um arquivo por tabela (hub_clientes.json ...): lista de linhas {id, dados, criado_em, ...}."""

    def __init__(self, pasta: Path) -> None:
        self.pasta = pasta

    def carregar(self, colecao: str) -> list[LinhaLegada]:
        arquivo = self.pasta / f"{colecao}.json"
        if not arquivo.exists():
            return []
        return [_linha(r) for r in json.loads(arquivo.read_text(encoding="utf-8"))]


class OrigemPostgres:
    """Lê direto do Postgres do Supabase (connection string de leitura)."""

    def __init__(self, url: str) -> None:
        self.url = url

    def carregar(self, colecao: str) -> list[LinhaLegada]:
        import psycopg
        from psycopg.rows import dict_row

        if colecao not in COLECOES:
            raise ValueError(colecao)
        with psycopg.connect(self.url, row_factory=dict_row) as con:
            if colecao == "hub_membros":
                linhas = con.execute("select email as id, to_jsonb(m) as dados from public.hub_membros m").fetchall()
            else:
                linhas = con.execute(f"select * from public.{colecao}").fetchall()  # noqa: S608 - nome validado acima
        return [_linha(r) for r in linhas]


# ----------------------------------------------------------------------------- limpeza de valores
def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower().strip()


def texto(v: Any) -> str | None:
    s = str(v).strip() if v is not None else ""
    return s or None


def dinheiro(v: Any) -> Decimal:
    if v in (None, ""):
        return Decimal("0.00")
    try:
        return Decimal(str(v).replace(",", ".")).quantize(Decimal("0.01"))
    except InvalidOperation:
        return Decimal("0.00")


def quantidade(v: Any) -> Decimal:
    try:
        q = Decimal(str(v).replace(",", "."))
    except InvalidOperation:
        return Decimal("1")
    return q if q > 0 else Decimal("1")


def data(v: Any) -> date | None:
    if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v[:10] if len(v) >= 10 else v):
        try:
            return date.fromisoformat(v[:10])
        except ValueError:
            return None
    return None


def escolher(v: Any, validos: set[str], padrao: str | None = None) -> str | None:
    return v if v in validos else padrao


def acrescentar_obs(obs: str | None, nota: str) -> str:
    return f"{obs}\n{nota}" if obs else nota


def parcela_do_texto(descricao: str) -> tuple[int, int] | None:
    """'Manutenção mensal · Portal · 3/12' -> (3, 12)."""
    m = re.search(r"(\d+)/(\d+)\s*$", descricao or "")
    if m and 1 <= int(m[1]) <= int(m[2]):
        return int(m[1]), int(m[2])
    return None


def limpar_cliente(d: dict[str, Any], rel: Relatorio) -> dict[str, Any]:
    obs = texto(d.get("obs"))
    documento = re.sub(r"\D", "", str(d.get("cnpj") or ""))
    tipo = "PF" if len(documento) == 11 else "PJ"
    if documento and not documento_valido(tipo, documento):
        obs = acrescentar_obs(obs, f"[CNPJ legado inválido: {d.get('cnpj')}]")
        rel.avisar(f"Cliente '{d.get('nome')}': CNPJ inválido '{d.get('cnpj')}' movido para as observações.")
        documento = ""
    origem = texto(d.get("origem"))
    if origem and origem not in ORIGENS:
        obs = acrescentar_obs(obs, f"[origem legado: {origem}]")
        origem = "Outro"
    return {
        "nome": (texto(d.get("nome")) or "(sem nome)")[:150], "tipo_pessoa": tipo, "cpf_cnpj": documento or None, "segmento": texto(d.get("segmento")),
        "contato": texto(d.get("contato")), "cargo": texto(d.get("cargo")), "telefone": texto(d.get("telefone")),
        "email": texto(d.get("email")), "cidade": texto(d.get("cidade")), "origem": origem, "obs": obs,  # cidade: resolvida em município pelo importador
    }  # fmt: skip


def limpar_produto(d: dict[str, Any]) -> dict[str, Any]:
    tipo = d.get("tipo") if d.get("tipo") in TIPOS_RECEITA else "outro"
    return {
        "nome": texto(d.get("nome")) or "(sem nome)", "tipo": tipo, "unidade": texto(d.get("unidade")) or "projeto",
        "preco": max(dinheiro(d.get("preco")), Decimal("0")), "ativo": d.get("ativo") is not False,
        "descricao": texto(d.get("descricao")),
    }  # fmt: skip


def limpar_negocio(d: dict[str, Any], rel: Relatorio) -> dict[str, Any]:
    etapa = d.get("etapa") or "lead"
    obs = texto(d.get("obs"))
    motivo = d.get("motivoPerda") or d.get("motivo")
    if etapa == "perdido":
        if motivo not in MOTIVOS:
            motivo = "Sem resposta"
            rel.avisar(f"Negócio '{d.get('titulo')}': perdido sem motivo válido; usado 'Sem resposta'.")
    else:
        motivo = None
    origem = texto(d.get("origem"))
    return {
        "titulo": texto(d.get("titulo")) or "(sem título)", "etapa": etapa, "valor": max(dinheiro(d.get("valor")), Decimal(0)),
        "mensal": max(dinheiro(d.get("mensal")), Decimal(0)), "previsao": data(d.get("previsao")),
        "origem": origem if origem in ORIGENS else None, "motivo_perda": motivo, "obs": obs,
        "fechado_em": (data(d.get("fechadoEm")) or data(d.get("atualizadoEm"))) if etapa == "ganho" else None,
    }  # fmt: skip


def limpar_itens(d: dict[str, Any]) -> list[dict[str, Any]]:
    itens = []
    for i in d.get("itens") or []:
        preco = i.get("preco") if i.get("preco") is not None else i.get("precoUnitario")
        itens.append({
            "descricao": texto(i.get("descricao")) or "Item", "qtd": quantidade(i.get("qtd")),
            "preco_unitario": max(dinheiro(preco), Decimal(0)), "mensal": bool(i.get("mensal")),
            "produto_legado": texto(i.get("produtoId")),
        })  # fmt: skip
    return itens


def limpar_orcamento(d: dict[str, Any]) -> dict[str, Any]:
    status = (
        d.get("status")
        if d.get("status") in {"rascunho", "enviado", "aprovado", "recusado"}
        else "enviado"
        if d.get("status") == "vencido"
        else "rascunho"
    )
    validade = int(dinheiro(d.get("validade"))) or 15
    return {
        "numero": texto(d.get("numero")), "data": data(d.get("data")) or date.today(), "validade_dias": max(validade, 1),
        "status": status, "desconto": max(dinheiro(d.get("desconto")), Decimal(0)), "obs": texto(d.get("obs")),
        "aprovado_em": (data(d.get("aprovadoEm")) or data(d.get("data"))) if status == "aprovado" else None,
    }  # fmt: skip


def limpar_lancamento(d: dict[str, Any]) -> dict[str, Any]:
    vencimento = data(d.get("data")) or date.today()
    status = "recebido" if d.get("status") == "recebido" else "previsto"
    return {
        "tipo": d.get("tipo") if d.get("tipo") in TIPOS_RECEITA else "outro",
        "descricao": texto(d.get("descricao")) or "(sem descrição)", "valor": max(dinheiro(d.get("valor")), Decimal(0)),
        "vencimento": vencimento, "status": status, "nf": texto(d.get("nf")),
        "recebido_em": (data(d.get("recebidoEm")) or vencimento) if status == "recebido" else None,
    }  # fmt: skip


def limpar_despesa(d: dict[str, Any]) -> dict[str, Any]:
    dia = data(d.get("data")) or date.today()
    status = "a_pagar" if d.get("status") == "a_pagar" else "pago"
    return {
        "data": dia, "descricao": texto(d.get("descricao")) or texto(d.get("categoria")) or "Despesa",
        "valor": max(dinheiro(d.get("valor")), Decimal(0)), "obs": texto(d.get("obs")), "status": status,
        "pago_em": (data(d.get("pagoEm")) or dia) if status == "pago" else None, "fornecedor": texto(d.get("fornecedor")),
        "categoria": texto(d.get("categoria")),
    }  # fmt: skip


def limpar_investimento(d: dict[str, Any]) -> dict[str, Any]:
    forma = d.get("forma") if d.get("forma") in FORMAS else "Outro"
    return {
        "data": data(d.get("data")) or date.today(), "descricao": texto(d.get("descricao")) or "Investimento",
        "valor": max(dinheiro(d.get("valor")), Decimal(0)), "forma": forma, "obs": texto(d.get("obs")),
        "investidor": texto(d.get("investidor")) or "Não informado",
    }  # fmt: skip


def limpar_projeto(d: dict[str, Any], rel: Relatorio) -> dict[str, Any]:
    inicio, entrega = data(d.get("inicio")), data(d.get("entrega"))
    if inicio and entrega and entrega < inicio:
        rel.avisar(f"Projeto '{d.get('titulo')}': entrega antes do início; entrega descartada.")
        entrega = None
    etapas = []
    for e in d.get("etapas") or []:
        ini, fim = data(e.get("inicio")), data(e.get("fim"))
        if ini and fim and fim < ini:
            fim = None
        etapas.append({
            "titulo": texto(e.get("titulo")) or "Etapa", "status": e.get("status") if e.get("status") in {"a_fazer", "andamento", "concluida"} else "a_fazer",
            "inicio": ini, "fim": fim, "descricao": texto(e.get("descricao")), "entregaveis": texto(e.get("entregaveis")),
            "responsavel": texto(e.get("responsavel")),
        })  # fmt: skip
    return {
        "titulo": texto(d.get("titulo")) or "(sem título)",
        "status": d.get("status") if d.get("status") in {"planejamento", "construcao", "validacao", "entregue", "pausado"} else "planejamento",
        "inicio": inicio, "entrega": entrega, "objetivo": texto(d.get("objetivo")), "escopo": texto(d.get("escopo")),
        "fora_escopo": texto(d.get("foraEscopo")), "pos_entrega": texto(d.get("posEntrega")), "etapas": etapas,
        "responsavel": texto(d.get("responsavel")),
    }  # fmt: skip


def limpar_tarefa(d: dict[str, Any], atualizado_em: datetime | None) -> dict[str, Any]:
    coluna = d.get("coluna") if d.get("coluna") in {"a_fazer", "fazendo", "revisao", "concluido"} else "a_fazer"
    concluida = _data_hora(d.get("concluidaEm"))
    concluida = (concluida or atualizado_em or datetime.now().astimezone()) if coluna == "concluido" else None
    return {
        "titulo": texto(d.get("titulo")) or "(sem título)", "coluna": coluna, "prazo": data(d.get("prazo")),
        "prioridade": d.get("prioridade") if d.get("prioridade") in {"alta", "media", "baixa"} else "media",
        "descricao": texto(d.get("descricao")), "concluida_em": concluida,
        "checklist": [{"texto": texto(i.get("texto")) or "Item", "feito": bool(i.get("feito"))} for i in d.get("checklist") or []],
    }  # fmt: skip

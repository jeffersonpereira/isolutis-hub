from sqlalchemy import exists, extract, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.domain.constantes import ETAPAS_ABERTAS
from app.domain.datas import adicionar_meses, hoje
from app.domain.dinheiro import ZERO
from app.models import LancamentoReceita, Negocio, Orcamento, OrcamentoItem, ParceiroPapel
from app.models.posvenda import Projeto, ProjetoEtapa

ABERTAS = [e.value for e in ETAPAS_ABERTAS]


async def _financeiro(sessao: AsyncSession) -> dict:
    """Bloco `financeiro`: recebimentos dos últimos 12 meses e lançamentos vencidos."""
    h = hoje()
    primeiro = adicionar_meses(h.replace(day=1), -11)
    ano_mes = (extract("year", LancamentoReceita.vencimento), extract("month", LancamentoReceita.vencimento))
    linhas = await sessao.execute(
        select(
            *ano_mes,
            func.coalesce(func.sum(LancamentoReceita.valor).filter(LancamentoReceita.status == "recebido"), 0),
            func.coalesce(func.sum(LancamentoReceita.valor).filter(LancamentoReceita.status != "recebido"), 0),
            func.coalesce(func.sum(LancamentoReceita.valor).filter(LancamentoReceita.tipo == "mensal"), 0),
        )
        .where(LancamentoReceita.vencimento >= primeiro)
        .group_by(*ano_mes)
    )
    por_mes = {(int(a), int(m)): (r, p, rec) for a, m, r, p, rec in linhas.all()}
    serie, d = [], primeiro
    for _ in range(12):
        recebido, previsto, _rec = por_mes.get((d.year, d.month), (ZERO, ZERO, ZERO))
        serie.append({"ano": d.year, "mes": d.month, "recebido": recebido, "previsto": previsto})
        d = adicionar_meses(d, 1)
    r_mes, p_mes, rec_mes = por_mes.get((h.year, h.month), (ZERO, ZERO, ZERO))

    alerta_lancamentos = (
        await sessao.execute(
            select(
                func.count().label("quantidade"),
                func.coalesce(func.array_agg(LancamentoReceita.id), text("ARRAY[]::uuid[]")).label("ids"),
            ).where(
                LancamentoReceita.vencimento < func.current_date() - text("INTERVAL '3 days'"),
                LancamentoReceita.status != "recebido",
            )
        )
    ).one()
    n_lancamentos = await sessao.scalar(select(func.count()).select_from(LancamentoReceita))
    return {
        "recebido_no_mes": r_mes,
        "previsto_no_mes": r_mes + p_mes,
        "recorrente_no_mes": rec_mes,
        "serie": serie,
        "alertas": {
            "lancamentos_vencidos": {"quantidade": alerta_lancamentos.quantidade, "ids": list(alerta_lancamentos.ids or [])}
        },
        "_vazio": not n_lancamentos,
    }


async def _comercial(sessao: AsyncSession) -> dict:
    """Bloco `comercial`: funil, fechamentos, orçamentos aguardando e orçamentos parados."""
    # --- funil: agregação via GROUP BY (sem carregar objetos em memória) ---
    funil_rows = (
        await sessao.execute(
            select(
                Negocio.etapa,
                func.count().label("quantidade"),
                func.coalesce(func.sum(Negocio.valor), 0).label("soma_valor"),
                func.coalesce(func.sum(Negocio.mensal), 0).label("soma_mensal"),
            )
            .where(Negocio.etapa.in_(ABERTAS))
            .group_by(Negocio.etapa)
        )
    ).all()

    por_etapa_map: dict[str, dict] = {}
    for row in funil_rows:
        por_etapa_map[row.etapa] = {
            "etapa": row.etapa,
            "quantidade": row.quantidade,
            # Valor em aberto considera o projeto mais 12 meses de manutenção.
            "valor": row.soma_valor + 12 * row.soma_mensal,
        }

    por_etapa = [
        por_etapa_map.get(etapa, {"etapa": etapa, "quantidade": 0, "valor": ZERO})
        for etapa in ABERTAS
    ]

    funil_abertos = sum(e["quantidade"] for e in por_etapa)
    funil_valor = sum((e["soma_valor"] for e in funil_rows), ZERO)
    funil_mensal = sum((e["soma_mensal"] for e in funil_rows), ZERO)

    # --- ganhos / perdidos / conversão ---
    resultado_fechados = (
        await sessao.execute(
            select(
                Negocio.etapa,
                func.count().label("quantidade"),
            )
            .where(Negocio.etapa.in_(["ganho", "perdido"]))
            .group_by(Negocio.etapa)
        )
    ).all()
    fechados_map = {row.etapa: row.quantidade for row in resultado_fechados}
    ganhos = fechados_map.get("ganho", 0)
    perdidos = fechados_map.get("perdido", 0)

    # --- próximos fechamentos (mantém joinedload para acessar cliente.nome) ---
    proximos = (
        await sessao.scalars(
            select(Negocio)
            .options(joinedload(Negocio.cliente))
            .where(Negocio.etapa.in_(ABERTAS), Negocio.previsao.isnot(None))
            .order_by(Negocio.previsao)
            .limit(6)
        )
    ).all()

    # --- orçamentos aguardando resposta: COUNT + valor direto via subquery ---
    item_subtotal = (
        select(
            OrcamentoItem.orcamento_id,
            func.coalesce(
                func.sum(
                    OrcamentoItem.qtd * OrcamentoItem.preco_unitario
                ).filter(OrcamentoItem.mensal == False),  # noqa: E712
                0,
            ).label("total_projeto"),
        )
        .group_by(OrcamentoItem.orcamento_id)
        .subquery()
    )
    orc_rows = (
        await sessao.execute(
            select(
                func.count().label("quantidade"),
                func.coalesce(func.sum(item_subtotal.c.total_projeto), 0).label("soma_valor"),
            )
            .select_from(Orcamento)
            .outerjoin(item_subtotal, Orcamento.id == item_subtotal.c.orcamento_id)
            .where(Orcamento.status == "enviado")
        )
    ).one()

    # Orçamentos para o painel (lista resumida, máx 6)
    aguardando_lista = (
        await sessao.scalars(
            select(Orcamento)
            .options(joinedload(Orcamento.cliente), selectinload(Orcamento.itens))
            .where(Orcamento.status == "enviado")
            .order_by(Orcamento.numero.desc())
            .limit(6)
        )
    ).all()

    n_clientes = await sessao.scalar(
        select(func.count()).select_from(ParceiroPapel).where(ParceiroPapel.papel == "cliente")
    )

    # --- alertas: orçamentos sem resposta há mais de 15 dias ---
    alerta_orcamentos = (
        await sessao.execute(
            select(
                func.count().label("quantidade"),
                func.coalesce(func.array_agg(Orcamento.id), text("ARRAY[]::uuid[]")).label("ids"),
            ).where(
                Orcamento.status == "enviado",
                Orcamento.data < func.current_date() - text("INTERVAL '15 days'"),
            )
        )
    ).one()

    return {
        "funil_abertos": funil_abertos,
        "funil_valor": funil_valor,
        "funil_mensal": funil_mensal,
        "ganhos": ganhos,
        "perdidos": perdidos,
        "conversao_pct": round(100 * ganhos / (ganhos + perdidos)) if ganhos + perdidos else None,
        "orcamentos_aguardando_qtd": orc_rows.quantidade,
        "orcamentos_aguardando_valor": orc_rows.soma_valor,
        "por_etapa": por_etapa,
        "proximos_fechamentos": [
            {
                "id": n.id,
                "titulo": n.titulo,
                "cliente_nome": n.cliente.nome,
                "etapa": n.etapa,
                "valor": n.valor,
                "mensal": n.mensal,
                "previsao": n.previsao,
            }
            for n in proximos
        ],  # fmt: skip
        "orcamentos_aguardando": [
            {
                "id": o.id,
                "numero": o.numero,
                "cliente_nome": o.cliente_nome,
                "data": o.data,
                "total_projeto": o.total_projeto,
            }
            for o in aguardando_lista
        ],
        "alertas": {
            "orcamentos_parados": {"quantidade": alerta_orcamentos.quantidade, "ids": list(alerta_orcamentos.ids or [])}
        },
        "_vazio": not (n_clientes or funil_abertos + ganhos + perdidos),
    }


async def _projetos_atrasados(sessao: AsyncSession) -> dict:
    """Alerta de projetos com entrega atrasada (`base`: projetos são abertos a todos os papéis)."""
    try:
        alerta = (
            await sessao.execute(
                select(
                    func.count().label("quantidade"),
                    func.coalesce(func.array_agg(Projeto.id), text("ARRAY[]::uuid[]")).label("ids"),
                ).where(
                    Projeto.entrega < func.current_date(),
                    exists(
                        select(ProjetoEtapa.id).where(
                            ProjetoEtapa.projeto_id == Projeto.id,
                            ProjetoEtapa.status != "concluida",
                        )
                    ),
                )
            )
        ).one()
        return {"quantidade": alerta.quantidade, "ids": list(alerta.ids or [])}
    except Exception:
        return {"quantidade": 0, "ids": []}


async def montar(sessao: AsyncSession, permissoes: frozenset[str] = frozenset({"base"})) -> dict:
    """Painel com apenas os blocos que as permissões do papel autorizam; os demais campos ficam ausentes.

    `base`: período, alerta de projetos atrasados e `banco_vazio`. `financeiro`: recebimentos e lançamentos vencidos.
    `comercial`: funil, fechamentos, orçamentos. `banco_vazio` só considera o que o papel pode ver; sem
    nenhum dos dois blocos é sempre falso (revela no máximo se há dados, nunca valores).
    """
    h = hoje()
    resultado: dict = {"ano": h.year, "mes": h.month}
    vazios: list[bool] = []
    alertas: dict = {}

    if "financeiro" in permissoes:
        bloco = await _financeiro(sessao)
        vazios.append(bloco.pop("_vazio"))
        alertas.update(bloco.pop("alertas"))
        resultado.update(bloco)
    if "comercial" in permissoes:
        bloco = await _comercial(sessao)
        vazios.append(bloco.pop("_vazio"))
        alertas.update(bloco.pop("alertas"))
        resultado.update(bloco)

    alertas["projetos_atrasados"] = await _projetos_atrasados(sessao)
    resultado["alertas"] = alertas
    resultado["banco_vazio"] = bool(vazios) and all(vazios)
    return resultado

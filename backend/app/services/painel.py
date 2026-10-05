from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.constantes import ETAPAS_ABERTAS
from app.domain.datas import adicionar_meses, hoje
from app.domain.dinheiro import ZERO
from app.models import LancamentoReceita, Negocio, ParceiroPapel
from app.services import orcamentos as svc_orcamentos

ABERTAS = [e.value for e in ETAPAS_ABERTAS]


async def montar(sessao: AsyncSession) -> dict:
    h = hoje()

    # --- faturamento: últimos 12 meses (inclui o atual) ---
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

    # --- funil ---
    negocios = (await sessao.scalars(select(Negocio).options(joinedload(Negocio.cliente)))).all()
    abertos = [n for n in negocios if n.etapa in ABERTAS]
    ganhos = sum(1 for n in negocios if n.etapa == "ganho")
    perdidos = sum(1 for n in negocios if n.etapa == "perdido")
    por_etapa = []
    for etapa in ABERTAS:
        ns = [n for n in abertos if n.etapa == etapa]
        # Valor em aberto considera o projeto mais 12 meses de manutenção.
        por_etapa.append(
            {"etapa": etapa, "quantidade": len(ns), "valor": sum((n.valor + 12 * n.mensal for n in ns), ZERO)}
        )
    proximos = sorted((n for n in abertos if n.previsao), key=lambda n: n.previsao)[:6]

    # --- orçamentos aguardando resposta ---
    aguardando = [o for o in await svc_orcamentos.listar(sessao) if o.status_exibido == "enviado"]

    n_clientes = await sessao.scalar(
        select(func.count()).select_from(ParceiroPapel).where(ParceiroPapel.papel == "cliente")
    )
    n_lancamentos = await sessao.scalar(select(func.count()).select_from(LancamentoReceita))
    return {
        "ano": h.year,
        "mes": h.month,
        "recebido_no_mes": r_mes,
        "previsto_no_mes": r_mes + p_mes,
        "recorrente_no_mes": rec_mes,
        "funil_abertos": len(abertos),
        "funil_valor": sum((n.valor for n in abertos), ZERO),
        "funil_mensal": sum((n.mensal for n in abertos), ZERO),
        "ganhos": ganhos,
        "perdidos": perdidos,
        "conversao_pct": round(100 * ganhos / (ganhos + perdidos)) if ganhos + perdidos else None,
        "orcamentos_aguardando_qtd": len(aguardando),
        "orcamentos_aguardando_valor": sum((o.total_projeto for o in aguardando), ZERO),
        "banco_vazio": not (n_clientes or negocios or n_lancamentos),
        "serie": serie,
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
            for o in aguardando[:6]
        ],
    }

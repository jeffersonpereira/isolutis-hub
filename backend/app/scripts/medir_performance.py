#!/usr/bin/env python3
"""Medição de performance: latência p50/p95, tamanho de índices, leituras/escrita.

Executar após backfill e ANALYZE, contra cópia representativa de produção.
Registra métricas por empresa (pequena, grande) para baseline.

Uso:
    python -m app.scripts.medir_performance
"""

import asyncio
import statistics
import time
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import criar_engine
from app.models import (
    Empresa,
    Despesa,
    LancamentoReceita,
    Negocio,
    Orcamento,
    Parceiro,
    Projeto,
    Tarefa,
)


class MedidorPerformance:
    """Coleta métricas de performance com RLS ativo."""

    def __init__(self):
        self.metricas = {
            "parceiro_listar": [],
            "negocio_listar": [],
            "orcamento_numero": [],
            "receita_periodo": [],
            "despesa_periodo": [],
            "tarefa_kanban": [],
            "filtro_tags": [],
            "join_negocio_cliente": [],
            "agregacao_despesa": [],
        }

    def registrar(self, operacao: str, duracao_ms: float):
        """Registrar duração de operação em ms."""
        self.metricas[operacao].append(duracao_ms)

    def relatorio(self):
        """Gerar relatório de métricas."""
        print("\n" + "=" * 80)
        print("RELATÓRIO DE PERFORMANCE")
        print("=" * 80)

        for op, durações in self.metricas.items():
            if not durações:
                print(f"\n{op}: SEM DADOS")
                continue

            durações_sorted = sorted(durações)
            n = len(durações_sorted)
            p50 = durações_sorted[n // 2]
            p95 = durações_sorted[int(n * 0.95)] if n > 1 else durações_sorted[0]
            media = statistics.mean(durações)
            minimo = min(durações)
            maximo = max(durações)

            print(f"\n{op}")
            print(f"  Execuções: {n}")
            print(f"  P50: {p50:.2f} ms")
            print(f"  P95: {p95:.2f} ms")
            print(f"  Média: {media:.2f} ms")
            print(f"  Mín: {minimo:.2f} ms | Máx: {maximo:.2f} ms")


async def medir_listar_parceiros(sessao: AsyncSession, empresa_id: UUID, medidor: MedidorPerformance, n_iteracoes: int = 10):
    """Medir latência de listagem de parceiros."""
    for _ in range(n_iteracoes):
        inicio = time.perf_counter()
        await sessao.execute(
            select(Parceiro).where(Parceiro.empresa_id == empresa_id).order_by(Parceiro.nome, Parceiro.id).limit(50)
        )
        duracao = (time.perf_counter() - inicio) * 1000
        medidor.registrar("parceiro_listar", duracao)


async def medir_listar_negocios(sessao: AsyncSession, empresa_id: UUID, medidor: MedidorPerformance, n_iteracoes: int = 10):
    """Medir latência de listagem de negócios."""
    for _ in range(n_iteracoes):
        inicio = time.perf_counter()
        await sessao.execute(
            select(Negocio)
            .where(Negocio.empresa_id == empresa_id)
            .order_by(Negocio.etapa, Negocio.previsao, Negocio.id)
            .limit(50)
        )
        duracao = (time.perf_counter() - inicio) * 1000
        medidor.registrar("negocio_listar", duracao)


async def medir_orcamento_numero(sessao: AsyncSession, empresa_id: UUID, medidor: MedidorPerformance, n_iteracoes: int = 10):
    """Medir latência de busca de orçamento por número (unique)."""
    # Assumindo que há orçamentos com números 1, 2, 3, etc.
    for i in range(1, n_iteracoes + 1):
        inicio = time.perf_counter()
        await sessao.scalar(
            select(Orcamento).where(Orcamento.empresa_id == empresa_id, Orcamento.numero == i)
        )
        duracao = (time.perf_counter() - inicio) * 1000
        medidor.registrar("orcamento_numero", duracao)


async def medir_receita_periodo(sessao: AsyncSession, empresa_id: UUID, medidor: MedidorPerformance, n_iteracoes: int = 10):
    """Medir latência de listagem de receitas por período."""
    hoje = date.today()
    for mes in range(1, n_iteracoes + 1):
        inicio_mes = date(hoje.year, mes if mes <= 12 else mes % 12, 1)
        fim_mes = inicio_mes + timedelta(days=32)
        fim_mes = fim_mes.replace(day=1) - timedelta(days=1)

        inicio = time.perf_counter()
        await sessao.execute(
            select(LancamentoReceita)
            .where(
                LancamentoReceita.empresa_id == empresa_id,
                LancamentoReceita.vencimento >= inicio_mes,
                LancamentoReceita.vencimento < fim_mes,
            )
            .order_by(LancamentoReceita.vencimento, LancamentoReceita.id)
            .limit(100)
        )
        duracao = (time.perf_counter() - inicio) * 1000
        medidor.registrar("receita_periodo", duracao)


async def medir_despesa_periodo(sessao: AsyncSession, empresa_id: UUID, medidor: MedidorPerformance, n_iteracoes: int = 10):
    """Medir latência de listagem de despesas por período."""
    hoje = date.today()
    for mes in range(1, n_iteracoes + 1):
        inicio_mes = date(hoje.year, mes if mes <= 12 else mes % 12, 1)
        fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        inicio = time.perf_counter()
        await sessao.execute(
            select(Despesa)
            .where(
                Despesa.empresa_id == empresa_id,
                Despesa.data >= inicio_mes,
                Despesa.data < fim_mes,
            )
            .order_by(Despesa.data, Despesa.id)
            .limit(100)
        )
        duracao = (time.perf_counter() - inicio) * 1000
        medidor.registrar("despesa_periodo", duracao)


async def medir_tarefa_kanban(sessao: AsyncSession, empresa_id: UUID, medidor: MedidorPerformance, n_iteracoes: int = 10):
    """Medir latência de listagem de tarefas por coluna (kanban)."""
    colunas = ["a_fazer", "em_progresso", "em_revisao", "feito"]
    for i in range(n_iteracoes):
        coluna = colunas[i % len(colunas)]
        inicio = time.perf_counter()
        await sessao.execute(
            select(Tarefa)
            .where(Tarefa.empresa_id == empresa_id, Tarefa.coluna == coluna)
            .order_by(Tarefa.prioridade_ordem, Tarefa.prazo, Tarefa.id)
            .limit(50)
        )
        duracao = (time.perf_counter() - inicio) * 1000
        medidor.registrar("tarefa_kanban", duracao)


async def relatorio_tamanho_indices(sessao: AsyncSession):
    """Relatorio de tamanho de índices."""
    print("\n" + "=" * 80)
    print("TAMANHO DE ÍNDICES")
    print("=" * 80)

    resultado = await sessao.execute(
        text("""
        SELECT
            schemaname,
            tablename,
            indexname,
            pg_size_pretty(pg_relation_size(indexrelid)) as tamanho
        FROM pg_indexes
        WHERE schemaname = 'public'
            AND tablename IN ('parceiro', 'negocio', 'orcamento', 'lancamento_receita', 'despesa', 'projeto', 'tarefa')
        ORDER BY pg_relation_size(indexrelid) DESC;
        """)
    )

    for row in resultado.fetchall():
        schema, tabela, indice, tamanho = row
        print(f"{tabela}.{indice}: {tamanho}")


async def relatorio_tamanho_tabelas(sessao: AsyncSession):
    """Relatório de tamanho de tabelas."""
    print("\n" + "=" * 80)
    print("TAMANHO DE TABELAS")
    print("=" * 80)

    resultado = await sessao.execute(
        text("""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as tamanho
        FROM pg_stat_user_tables
        WHERE schemaname = 'public'
            AND tablename IN ('parceiro', 'negocio', 'orcamento', 'lancamento_receita', 'despesa', 'projeto', 'tarefa')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """)
    )

    for row in resultado.fetchall():
        schema, tabela, tamanho = row
        print(f"{tabela}: {tamanho}")


async def main():
    """Medir performance."""
    engine = criar_engine()

    async with engine.begin() as conexao:
        # Não usar transação, apenas sessão para leitura
        from sqlalchemy.ext.asyncio import AsyncSession as Session

        async with Session(conexao) as sessao:
            # Preparar contexto RLS
            await sessao.execute(text("SET app.empresa_id = 'UUID-EMPRESA-PEQUENA'::uuid"))

            # Obter empresa para testes
            resultado = await sessao.scalar(
                select(Empresa.id).where(Empresa.nome == "Test Tags").limit(1)
            )
            empresa_id = resultado or (await sessao.scalar(select(Empresa.id).limit(1)))

            if not empresa_id:
                print("ERRO: Nenhuma empresa encontrada para testes de performance")
                return

            print(f"Medindo performance para empresa: {empresa_id}")
            medidor = MedidorPerformance()

            # Executar medições
            print("\nMedindo latências...")
            await medir_listar_parceiros(sessao, empresa_id, medidor)
            await medir_listar_negocios(sessao, empresa_id, medidor)
            await medir_orcamento_numero(sessao, empresa_id, medidor)
            await medir_receita_periodo(sessao, empresa_id, medidor)
            await medir_despesa_periodo(sessao, empresa_id, medidor)
            await medir_tarefa_kanban(sessao, empresa_id, medidor)

            # Gerar relatórios
            medidor.relatorio()
            await relatorio_tamanho_tabelas(sessao)
            await relatorio_tamanho_indices(sessao)

            print("\n" + "=" * 80)
            print("INTERPRETAÇÃO")
            print("=" * 80)
            print("""
P50/P95 Latência:
  - < 100 ms: excelente
  - 100-500 ms: aceitável
  - > 500 ms: considerar índices ou particionamento

Tamanho de Índices:
  - Cada índice adicional aumenta write amplification
  - Manter apenas índices com benefício demonstrado
  - Verificar se índices candidatos reduzem latência p95

Write Amplification:
  - Monitorar latência de INSERT/UPDATE com múltiplos índices
  - Se degradação > 20%, reconsidar índices opcionais
            """)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

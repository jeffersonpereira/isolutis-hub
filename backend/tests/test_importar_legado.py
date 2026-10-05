from pathlib import Path

from sqlalchemy import func, select, text

from app.models import Despesa, Investimento, LancamentoReceita, Negocio, Orcamento, Parceiro, Projeto, Tarefa, Usuario
from app.scripts import legado as lg
from app.scripts.importar_legado import Importador

PASTA = Path(__file__).parent / "fixtures_legado"


async def test_importacao_completa_com_limpeza(sessao):
    rel = await Importador(sessao, lg.OrigemJson(PASTA)).importar()
    await sessao.flush()

    soraya = await sessao.scalar(select(Usuario).where(Usuario.email == "soydeoliveira@gmail.com"))
    assert soraya.admin and soraya.senha_hash is None and not soraya.senha_definida

    alfa, beta, dup = [
        await sessao.scalar(select(Parceiro).where(Parceiro.nome == n))
        for n in ("Distribuidora Alfa", "Beta", "Alfa Duplicada")
    ]
    assert (
        alfa.cpf_cnpj == "11222333000181" and alfa.criado_em.year == 2025 and alfa.atualizado_por is not None
    )  # carimbos preservados
    assert alfa.criado_por == soraya.id
    assert beta.cpf_cnpj is None and "CNPJ legado inválido" in beta.obs and beta.origem == "Outro"
    assert dup.cpf_cnpj is None and "duplicado" in dup.obs

    negocios = {n.titulo: n for n in (await sessao.scalars(select(Negocio))).all()}
    assert set(negocios) == {"Portal", "Perdido sem motivo"}  # o órfão não migra
    assert negocios["Perdido sem motivo"].motivo_perda == "Sem resposta"
    assert negocios["Portal"].responsavel_id == soraya.id and str(negocios["Portal"].fechado_em) == "2025-04-01"

    o1 = await sessao.scalar(select(Orcamento).where(Orcamento.numero == "2025-007"))
    assert o1.status == "aprovado" and str(o1.aprovado_em) == "2025-03-10"
    # orçamento de outro cliente com negócio alheio perde o vínculo e o status "vencido" volta a "enviado"
    o2 = await sessao.scalar(select(Orcamento).where(Orcamento.numero == "2025-008"))
    assert o2.negocio_id is None and o2.status == "enviado"
    # sequência de numeração avança para não colidir com os números migrados
    assert await sessao.scalar(text("select proximo_numero_orcamento(2025)")) == "2025-009"

    lancs = (await sessao.scalars(select(LancamentoReceita).order_by(LancamentoReceita.vencimento))).all()
    mensais = [x for x in lancs if x.tipo == "mensal"]
    assert [x.parcela for x in mensais] == [1, 2] and mensais[0].grupo_id == mensais[1].grupo_id
    avulso = next(x for x in lancs if x.descricao == "Avulso")
    assert float(avulso.valor) == 1500.5
    assert avulso.recebido_em is not None  # recebido sem data -> usa o vencimento

    assert await sessao.scalar(select(func.count()).select_from(Despesa)) == 2
    invs = (await sessao.scalars(select(Investimento))).all()
    assert len(invs) == 2
    projetos = (await sessao.scalars(select(Projeto))).all()
    por_titulo = {p.titulo: p for p in projetos}
    assert por_titulo["Portal"].entrega is None  # entrega < início descartada
    assert por_titulo["Portal"].negocio_id is not None and por_titulo["Segundo no mesmo negócio"].negocio_id is None
    tarefa = await sessao.scalar(select(Tarefa))
    assert tarefa.concluida_em is not None and tarefa.responsavel_id is not None

    assert rel.importados["hub_clientes"] == 3 and rel.importados["hub_negocios"] == 2
    avisos = "\n".join(rel.avisos)
    assert "cliente inexistente" in avisos and "perdido sem motivo" in avisos and "CNPJ" in avisos


async def test_importacao_e_idempotente(sessao):
    await Importador(sessao, lg.OrigemJson(PASTA)).importar()
    segunda = await Importador(sessao, lg.OrigemJson(PASTA)).importar()
    assert sum(segunda.importados.values()) == 0
    assert await sessao.scalar(select(func.count()).select_from(Parceiro)) == 3


def test_limpeza_de_valores():
    assert lg.dinheiro(None) == 0 and lg.dinheiro("abc") == 0
    assert lg.data("2025-13-45") is None and lg.data("") is None and str(lg.data("2025-02-03T10:00")) == "2025-02-03"
    assert lg.parcela_do_texto("Manutenção · 3/12") == (3, 12) and lg.parcela_do_texto("x 5/3") is None
    assert lg.sem_acento("  Sócio ÁÉ ") == "socio ae"

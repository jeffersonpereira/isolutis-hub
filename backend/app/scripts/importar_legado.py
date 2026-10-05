"""Migra os dados do sistema anterior (Supabase, tabelas hub_* em JSONB) para o schema relacional.

Uso:
  python -m app.scripts.importar_legado --json-dir ./export            # arquivos hub_<tabela>.json
  python -m app.scripts.importar_legado --origem-url postgresql://...  # lê direto do Postgres do Supabase
  python -m app.scripts.importar_legado --json-dir ./export --simular  # faz tudo e desfaz (relatório de avisos)

É idempotente: o mapeamento id antigo -> id novo fica em `legado_ids`; rodar de novo só importa o que falta.
Datas e autores originais são preservados (app.preservar_auditoria). Usuários importados ficam SEM senha:
um administrador define a senha de cada um na tela Equipe.
"""

import argparse
import asyncio
import re
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal, definir_empresa_da_transacao, definir_usuario_da_transacao
from app.models import (
    CategoriaDespesa,
    Despesa,
    Investidor,
    Investimento,
    LancamentoReceita,
    Municipio,
    Negocio,
    Orcamento,
    OrcamentoItem,
    Parceiro,
    ParceiroPapel,
    Produto,
    Projeto,
    ProjetoEtapa,
    Tarefa,
    TarefaChecklist,
    Usuario,
    UsuarioEmpresa,
)  # fmt: skip
from app.scripts import legado as lg
from app.services.parceiros import empresa_atual


class Importador:
    def __init__(self, sessao: AsyncSession, origem: lg.Origem, empresa_id: uuid.UUID) -> None:
        self.sessao, self.origem, self.empresa_id, self.rel = sessao, origem, empresa_id, lg.Relatorio()
        self.ids: dict[str, dict[str, uuid.UUID]] = defaultdict(dict)  # colecao -> id antigo -> id novo
        self.usuarios_por_email: dict[str, Usuario] = {}
        self.categorias: dict[str, CategoriaDespesa] = {}
        self.investidores: dict[str, Investidor] = {}

    # -- infraestrutura ---------------------------------------------------------------------
    async def _carregar_mapa(self) -> None:
        linhas = await self.sessao.execute(text("select colecao, legacy_id, novo_id from legado_ids"))
        for colecao, antigo, novo in linhas.all():
            self.ids[colecao][antigo] = novo

    async def _registrar(self, colecao: str, antigo: str, novo: uuid.UUID) -> None:
        self.ids[colecao][antigo] = novo
        await self.sessao.execute(
            text("insert into legado_ids (colecao, legacy_id, novo_id) values (:c, :a, :n)"),
            {"c": colecao, "a": antigo, "n": novo},
        )

    def _carimbos(self, linha: lg.LinhaLegada) -> dict[str, Any]:
        email = (linha.atualizado_por or linha.dados.get("alteradoPor") or "").lower()
        criador = str(linha.dados.get("criadoPor") or email or "").lower()
        autor = lambda e: self.usuarios_por_email[e].id if e in self.usuarios_por_email else None  # noqa: E731
        campos: dict[str, Any] = {"criado_por": autor(criador), "atualizado_por": autor(email)}
        if linha.criado_em:
            campos["criado_em"] = linha.criado_em
        if linha.atualizado_em:
            campos["atualizado_em"] = linha.atualizado_em
        return campos

    def _usuario_por_texto(self, valor: str | None, contexto: str) -> uuid.UUID | None:
        """Responsável escrito à mão -> usuário (nome completo, primeiro nome ou e-mail)."""
        if not valor:
            return None
        alvo = lg.sem_acento(valor)
        for u in self.usuarios_por_email.values():
            nome = lg.sem_acento(u.nome)
            if alvo in (nome, nome.split()[0], str(u.email).lower()) or alvo.split()[0] == nome.split()[0]:
                return u.id
        self.rel.avisar(f"{contexto}: responsável '{valor}' não corresponde a nenhum usuário; ficou em branco.")
        return None

    def _fk(self, colecao: str, antigo: Any) -> uuid.UUID | None:
        return self.ids[colecao].get(str(antigo)) if antigo else None

    async def _adicionar(self, colecao: str, linha: lg.LinhaLegada, obj: Any) -> None:
        self.sessao.add(obj)
        await self.sessao.flush()
        await self._registrar(colecao, linha.id, obj.id)
        self.rel.importados[colecao] += 1

    def _novas(self, colecao: str) -> list[lg.LinhaLegada]:
        todas = self.origem.carregar(colecao)
        novas = [x for x in todas if x.id not in self.ids[colecao]]
        self.rel.ja_existiam[colecao] += len(todas) - len(novas)
        return novas

    # -- coleções ---------------------------------------------------------------------------
    async def importar(self) -> lg.Relatorio:
        await self.sessao.execute(text("select set_config('app.preservar_auditoria', 'on', true)"))
        await self._carregar_mapa()
        for u in (await self.sessao.scalars(select(Usuario))).all():
            self.usuarios_por_email[str(u.email).lower()] = u
        for c in (await self.sessao.scalars(select(CategoriaDespesa))).all():
            self.categorias[lg.sem_acento(str(c.nome))] = c
        for i in (await self.sessao.scalars(select(Investidor))).all():
            self.investidores[lg.sem_acento(str(i.nome))] = i

        await self.membros()
        await self.clientes()
        await self.produtos()
        await self.negocios()
        await self.orcamentos()
        await self.faturamento()
        await self.despesas()
        await self.projetos()
        await self.tarefas()
        return self.rel

    async def membros(self) -> None:
        for linha in self._novas("hub_membros"):
            email = linha.id.lower()
            existente = self.usuarios_por_email.get(email)
            if existente:
                await self._registrar("hub_membros", linha.id, existente.id)
                usuario = existente
                papel = "admin" if bool(linha.dados.get("admin")) else "membro"
            else:
                nome = lg.texto(linha.dados.get("nome")) or email
                usuario = Usuario(email=email, nome=nome, admin=False, senha_hash=None)
                await self._adicionar("hub_membros", linha, usuario)
                self.usuarios_por_email[email] = usuario
                papel = "admin" if bool(linha.dados.get("admin")) else "membro"
            usuario.admin = False
            membership = await self.sessao.get(UsuarioEmpresa, (self.empresa_id, usuario.id))
            if membership is None:
                self.sessao.add(UsuarioEmpresa(empresa_id=self.empresa_id, usuario_id=usuario.id, papel=papel, ativo=usuario.ativo))

    async def _indice_de_municipios(self) -> dict[tuple[str, str | None], list[uuid.UUID]]:
        """(nome sem acento, UF) e (nome sem acento, None) -> ids; usado para casar a cidade em texto livre."""
        indice: dict[tuple[str, str | None], list[uuid.UUID]] = defaultdict(list)
        for m in (await self.sessao.scalars(select(Municipio))).all():
            nome = lg.sem_acento(m.nome)
            indice[(nome, m.uf)].append(m.id)
            indice[(nome, None)].append(m.id)
        return indice

    @staticmethod
    def _municipio_do_texto(
        cidade: str | None, indice: dict[tuple[str, str | None], list[uuid.UUID]]
    ) -> uuid.UUID | None:
        """ "Salvador", "Salvador/BA", "Salvador - BA": só aceita se o casamento for único."""
        if not cidade:
            return None
        achado = re.fullmatch(r"(.*?)\s*[/,-]\s*([A-Za-z]{2})\s*", cidade)
        nome, uf = (achado[1], achado[2].upper()) if achado else (cidade, None)
        ids = indice.get((lg.sem_acento(nome), uf), [])
        return ids[0] if len(ids) == 1 else None

    async def clientes(self) -> None:
        empresa = await empresa_atual(self.sessao)
        documentos_usados = {
            c
            for (c,) in (
                await self.sessao.execute(select(Parceiro.cpf_cnpj).where(Parceiro.cpf_cnpj.is_not(None)))
            ).all()
        }
        indice = await self._indice_de_municipios()
        for linha in self._novas("hub_clientes"):
            campos = lg.limpar_cliente(linha.dados, self.rel)
            cidade = campos.pop("cidade")
            if campos["cpf_cnpj"] in documentos_usados:
                campos["obs"] = lg.acrescentar_obs(campos["obs"], f"[CNPJ duplicado no legado: {campos['cpf_cnpj']}]")
                self.rel.avisar(
                    f"Cliente '{campos['nome']}': CNPJ {campos['cpf_cnpj']} repetido; mantido só no primeiro."
                )
                campos["cpf_cnpj"] = None
            if campos["cpf_cnpj"]:
                documentos_usados.add(campos["cpf_cnpj"])
            municipio_id = self._municipio_do_texto(cidade, indice)
            if cidade and municipio_id is None:
                campos["obs"] = lg.acrescentar_obs(campos["obs"], f"[cidade informada: {cidade}]")
            parceiro = Parceiro(
                empresa_id=empresa.id, municipio_id=municipio_id, papeis=[ParceiroPapel(papel="cliente")],
                **campos, **self._carimbos(linha),
            )  # fmt: skip
            await self._adicionar("hub_clientes", linha, parceiro)

    async def produtos(self) -> None:
        for linha in self._novas("hub_produtos"):
            await self._adicionar(
                "hub_produtos", linha, Produto(**lg.limpar_produto(linha.dados), **self._carimbos(linha))
            )

    def _cliente_ou_pular(self, linha: lg.LinhaLegada, colecao: str) -> uuid.UUID | None:
        cliente_id = self._fk("hub_clientes", linha.dados.get("clienteId"))
        if cliente_id is None:
            self.rel.avisar(
                f"{colecao} '{linha.dados.get('titulo') or linha.dados.get('numero') or linha.id}': cliente inexistente; não migrado."
            )
        return cliente_id

    async def negocios(self) -> None:
        for linha in self._novas("hub_negocios"):
            cliente_id = self._cliente_ou_pular(linha, "Negócio")
            if cliente_id is None:
                continue
            campos = lg.limpar_negocio(linha.dados, self.rel)
            responsavel = self._usuario_por_texto(
                lg.texto(linha.dados.get("responsavel")), f"Negócio '{campos['titulo']}'"
            )
            neg = Negocio(**campos, cliente_id=cliente_id, responsavel_id=responsavel, **self._carimbos(linha))
            await self._adicionar("hub_negocios", linha, neg)

    async def _negocio_do_cliente(self, antigo: Any, cliente_id: uuid.UUID, contexto: str) -> uuid.UUID | None:
        negocio_id = self._fk("hub_negocios", antigo)
        if negocio_id is None:
            return None
        negocio = await self.sessao.get(Negocio, negocio_id)
        if negocio and negocio.cliente_id != cliente_id:
            self.rel.avisar(f"{contexto}: negócio de outro cliente; vínculo removido.")
            return None
        return negocio_id

    async def orcamentos(self) -> None:
        for linha in self._novas("hub_orcamentos"):
            cliente_id = self._cliente_ou_pular(linha, "Orçamento")
            if cliente_id is None:
                continue
            campos = lg.limpar_orcamento(linha.dados)
            negocio_id = await self._negocio_do_cliente(
                linha.dados.get("negocioId"), cliente_id, f"Orçamento {campos['numero']}"
            )
            itens = lg.limpar_itens(linha.dados) or [
                {"descricao": "Item", "qtd": 1, "preco_unitario": 0, "mensal": False, "produto_legado": None}
            ]
            orc = Orcamento(**campos, cliente_id=cliente_id, negocio_id=negocio_id, itens=[], **self._carimbos(linha))
            for ordem, i in enumerate(itens, start=1):
                produto = i.pop("produto_legado")
                orc.itens.append(OrcamentoItem(**i, ordem=ordem, produto_id=self._fk("hub_produtos", produto)))
            await self._adicionar("hub_orcamentos", linha, orc)

    async def faturamento(self) -> None:
        series: dict[tuple, uuid.UUID] = {}
        for linha in self._novas("hub_faturamento"):
            cliente_id = self._cliente_ou_pular(linha, "Lançamento")
            if cliente_id is None:
                continue
            campos = lg.limpar_lancamento(linha.dados)
            ctx = f"Lançamento '{campos['descricao']}'"
            negocio_id = await self._negocio_do_cliente(linha.dados.get("negocioId"), cliente_id, ctx)
            orc_id = self._fk("hub_orcamentos", linha.dados.get("orcamentoId"))
            if orc_id and (await self.sessao.get(Orcamento, orc_id)).cliente_id != cliente_id:  # type: ignore[union-attr]
                orc_id = None
            serie = {}
            if p := lg.parcela_do_texto(campos["descricao"]):
                chave = (cliente_id, campos["tipo"], campos["valor"], campos["descricao"].rsplit(" ", 1)[0], p[1])
                serie = {"grupo_id": series.setdefault(chave, uuid.uuid4()), "parcela": p[0], "total_parcelas": p[1]}
            lanc = LancamentoReceita(
                **campos,
                cliente_id=cliente_id,
                negocio_id=negocio_id,
                orcamento_id=orc_id,
                **serie,
                **self._carimbos(linha),
            )
            try:
                async with self.sessao.begin_nested():
                    await self._adicionar("hub_faturamento", linha, lanc)
            except Exception:  # noqa: BLE001 - parcela duplicada na série: importa sem agrupar
                lanc = LancamentoReceita(
                    **campos, cliente_id=cliente_id, negocio_id=negocio_id, orcamento_id=orc_id, **self._carimbos(linha)
                )
                await self._adicionar("hub_faturamento", linha, lanc)

    async def _categoria(self, nome: str | None) -> CategoriaDespesa:
        chave = lg.sem_acento(nome or "outros")
        if chave not in self.categorias:
            cat = CategoriaDespesa(nome=nome or "Outros", ordem=100)
            self.sessao.add(cat)
            await self.sessao.flush()
            self.categorias[chave] = cat
        return self.categorias[chave]

    async def _investidor(self, nome: str) -> Investidor:
        chave = lg.sem_acento(nome)
        if chave not in self.investidores:
            inv = Investidor(nome=nome, usuario_id=self._usuario_por_texto_silencioso(nome))
            self.sessao.add(inv)
            await self.sessao.flush()
            self.investidores[chave] = inv
        return self.investidores[chave]

    def _usuario_por_texto_silencioso(self, nome: str) -> uuid.UUID | None:
        antes = len(self.rel.avisos)
        achado = self._usuario_por_texto(nome, "Investidor")
        del self.rel.avisos[antes:]
        usado = {i.usuario_id for i in self.investidores.values()}
        return None if achado in usado else achado

    async def despesas(self) -> None:
        series: dict[tuple, uuid.UUID] = {}
        for linha in self._novas("hub_despesas"):
            d = linha.dados
            if d.get("tipo") == "investimento":
                campos = lg.limpar_investimento(d)
                investidor = await self._investidor(campos.pop("investidor"))
                obj = Investimento(**campos, investidor_id=investidor.id, **self._carimbos(linha))
            else:
                campos = lg.limpar_despesa(d)
                categoria = await self._categoria(campos.pop("categoria"))
                serie = {}
                if p := lg.parcela_do_texto(campos["descricao"]):
                    chave = (campos["valor"], campos["descricao"].rsplit(" ", 1)[0], categoria.id, p[1])
                    serie = {
                        "grupo_id": series.setdefault(chave, uuid.uuid4()),
                        "parcela": p[0],
                        "total_parcelas": p[1],
                    }
                obj = Despesa(**campos, categoria_id=categoria.id, **serie, **self._carimbos(linha))
            await self._adicionar("hub_despesas", linha, obj)

    async def projetos(self) -> None:
        negocios_usados = {
            n
            for (n,) in (
                await self.sessao.execute(select(Projeto.negocio_id).where(Projeto.negocio_id.is_not(None)))
            ).all()
        }
        for linha in self._novas("hub_projetos"):
            cliente_id = self._cliente_ou_pular(linha, "Projeto")
            if cliente_id is None:
                continue
            campos = lg.limpar_projeto(linha.dados, self.rel)
            etapas = campos.pop("etapas")
            responsavel = self._usuario_por_texto(campos.pop("responsavel"), f"Projeto '{campos['titulo']}'")
            negocio_id = await self._negocio_do_cliente(
                linha.dados.get("negocioId"), cliente_id, f"Projeto '{campos['titulo']}'"
            )
            if negocio_id in negocios_usados:
                self.rel.avisar(f"Projeto '{campos['titulo']}': o negócio já tem outro projeto; vínculo removido.")
                negocio_id = None
            if negocio_id:
                negocios_usados.add(negocio_id)
            orc_id = self._fk("hub_orcamentos", linha.dados.get("orcamentoId"))
            if orc_id and (await self.sessao.get(Orcamento, orc_id)).cliente_id != cliente_id:  # type: ignore[union-attr]
                orc_id = None
            proj = Projeto(
                **campos,
                cliente_id=cliente_id,
                negocio_id=negocio_id,
                orcamento_id=orc_id,
                responsavel_id=responsavel,
                etapas=[],
                **self._carimbos(linha),
            )
            for ordem, e in enumerate(etapas, start=1):
                resp = self._usuario_por_texto(e.pop("responsavel"), f"Etapa '{e['titulo']}'")
                proj.etapas.append(ProjetoEtapa(**e, ordem=ordem, responsavel_id=resp))
            await self._adicionar("hub_projetos", linha, proj)

    async def tarefas(self) -> None:
        for linha in self._novas("hub_tarefas"):
            campos = lg.limpar_tarefa(linha.dados, linha.atualizado_em)
            checklist = campos.pop("checklist")
            resp = self.usuarios_por_email.get(str(linha.dados.get("responsavel") or "").lower())
            tarefa = Tarefa(
                **campos, responsavel_id=resp.id if resp else None, cliente_id=self._fk("hub_clientes", linha.dados.get("clienteId")),
                projeto_id=self._fk("hub_projetos", linha.dados.get("projetoId")), checklist=[], **self._carimbos(linha),
            )  # fmt: skip
            for ordem, i in enumerate(checklist, start=1):
                tarefa.checklist.append(TarefaChecklist(**i, ordem=ordem))
            await self._adicionar("hub_tarefas", linha, tarefa)


async def executar(origem: lg.Origem, simular: bool, empresa_id: uuid.UUID, usuario_id: uuid.UUID) -> lg.Relatorio:
    async with SessionLocal() as sessao:
        usuario = await sessao.get(Usuario, usuario_id)
        if usuario is None or not usuario.ativo:
            raise SystemExit("Usuário importador inexistente ou inativo.")
        await definir_usuario_da_transacao(sessao, usuario_id)
        associacao = await sessao.get(UsuarioEmpresa, (empresa_id, usuario_id))
        if associacao is None or not associacao.ativo or associacao.papel != "admin":
            raise SystemExit("O usuário importador precisa ser administrador ativo da empresa informada.")
        await definir_empresa_da_transacao(sessao, empresa_id)
        sessao.info["empresa_id"] = empresa_id
        rel = await Importador(sessao, origem, empresa_id).importar()
        if simular:
            await sessao.rollback()
        else:
            await sessao.commit()
    return rel


def imprimir(rel: lg.Relatorio, simular: bool) -> None:
    print("SIMULAÇÃO (nada foi gravado)" if simular else "IMPORTAÇÃO CONCLUÍDA")
    for colecao in lg.COLECOES:
        print(f"  {colecao:16} importados: {rel.importados[colecao]:4}   já existiam: {rel.ja_existiam[colecao]:4}")
    if rel.avisos:
        print(f"\n{len(rel.avisos)} aviso(s) para revisão:")
        for aviso in rel.avisos:
            print(f"  - {aviso}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    fonte = ap.add_mutually_exclusive_group(required=True)
    fonte.add_argument("--json-dir", type=Path, help="pasta com hub_<tabela>.json")
    fonte.add_argument("--origem-url", help="connection string (somente leitura) do Postgres do Supabase")
    ap.add_argument("--simular", action="store_true", help="executa e desfaz, só mostrando o relatório")
    ap.add_argument("--empresa-id", required=True, type=uuid.UUID, help="UUID da empresa proprietária dos registros importados")
    ap.add_argument("--usuario-id", required=True, type=uuid.UUID, help="UUID do administrador que autoriza a importação")
    args = ap.parse_args()
    origem = lg.OrigemJson(args.json_dir) if args.json_dir else lg.OrigemPostgres(args.origem_url)
    rel = asyncio.run(executar(origem, args.simular, args.empresa_id, args.usuario_id))
    imprimir(rel, args.simular)
    sys.exit(0)


if __name__ == "__main__":
    main()

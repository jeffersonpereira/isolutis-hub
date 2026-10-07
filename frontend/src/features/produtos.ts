import { api } from "@/api/endpoints";
import type { Produto, ProdutoEntrada } from "@/api/tipos";
import { brl, compararTexto } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { numero, paraCampo } from "@/core/numero";
import { $ } from "@/core/dom";
import { TIPOS, UNIDADES } from "@/domain/constantes";
import { dados, podeEscrever } from "@/state/estado";
import { recarregar, registrarVista } from "@/state/nucleo";
import { registrarAcao } from "@/ui/acoes";
import { area, campo, fv, inp, sel } from "@/ui/campos";
import { registrarConsulta } from "@/ui/conflito";
import { registrarAbertura } from "@/ui/eventos";
import { abrirGaveta } from "@/ui/gaveta";
import { linhaAutoria } from "@/ui/autoria";
import { botaoExcluir, botaoSalvar, espaco } from "@/ui/formularios";
import { excluir, gravar } from "@/ui/gravacao";
import { tentar } from "@/ui/erros";
import { toast } from "@/ui/toast";
import { melhorarFormulario } from "@/ui/acessibilidade";
import { botaoNovo } from "./comum";

registrarConsulta("produtos", (id) => dados.produtos.find((p) => p.id === id));

function vista(): Safe {
  const lista = [...dados.produtos].sort((a, b) => compararTexto(a.tipo, b.tipo) || compararTexto(a.nome, b.nome));
  const semPreco = lista.filter((p) => !numero(p.preco)).length;
  return html`<div class="head"><div><h1>Cadastro de produtos</h1><p>O que a iSolutis vende. Os preços daqui preenchem os orçamentos, e você pode ajustar em cada um.</p></div><div class="tools">${botaoNovo("novoProduto", "Novo produto")}</div></div>
  ${
    !lista.length
      ? html`<div class="empty"><b>Nenhum produto cadastrado</b>Você pode começar pelo catálogo do site: três faixas de sistema sob medida, as manutenções mensais correspondentes e consultoria. Os preços ficam em branco para você definir.${podeEscrever() ? html`<br><button class="btn primary" data-act="catalogo">Criar a partir do catálogo do site</button> <button class="btn" data-act="novoProduto">Cadastrar manualmente</button>` : ""}</div>`
      : html`${semPreco ? html`<div class="banner">${semPreco} ${semPreco === 1 ? "produto está" : "produtos estão"} sem preço de referência. Abra cada um para definir o valor.</div>` : ""}
  <div class="tbl-wrap"><table><thead><tr><th>Produto</th><th>Tipo</th><th class="r">Preço de referência</th><th>Situação</th></tr></thead><tbody>
    ${lista.map(
      (p) => html`<tr tabindex="0" data-open="produto:${p.id}"><td><b>${p.nome}</b>${p.descricao ? html`<div class="sub">${p.descricao}</div>` : ""}</td><td>${TIPOS[p.tipo] ?? "—"}</td>
      <td class="r num">${numero(p.preco) ? html`${brl(p.preco)} <span class="sub">/${p.unidade || UNIDADES[p.tipo] || "un."}</span>` : html`<span class="pill warn">definir</span>`}</td>
      <td>${p.ativo ? html`<span class="pill ok">Ativo</span>` : html`<span class="pill">Inativo</span>`}</td></tr>`,
    )}
  </tbody></table></div>`
  }`;
}

registrarVista({ id: "produtos", permissao: "comercial", nome: "Produtos", contagem: () => dados.produtos.length, desenhar: vista });

function formProduto(p?: Produto): void {
  abrirGaveta({
    titulo: p ? p.nome : "Novo produto",
    registro: p ? { recurso: "produtos", id: p.id, versao: p.versao } : null,
    autoria: linhaAutoria(p),
    corpo: html`<div class="fields">
      ${campo("Nome", inp("nome", p?.nome), true)}
      ${campo("Tipo", sel("tipo", Object.entries(TIPOS), p?.tipo ?? "projeto"))}${campo("Cobrado por", inp("unidade", p?.unidade ?? UNIDADES.projeto, 'placeholder="projeto, mês, hora…"'))}
      ${campo("Preço de referência (R$)", inp("preco", paraCampo(p?.preco), 'inputmode="decimal" placeholder="0,00"'))}${campo("Situação", sel("ativo", [["1", "Ativo"], ["0", "Inativo"]], p && !p.ativo ? "0" : "1"))}
      ${campo("Descrição", area("descricao", p?.descricao), true)}</div>`,
    rodape: html`${botaoSalvar()}${espaco}${botaoExcluir(!!p)}`,
    montar: (f, fechar, L) => {
      melhorarFormulario(f);
      (f.elements.namedItem("tipo") as HTMLSelectElement).addEventListener("change", () => {
        (f.elements.namedItem("unidade") as HTMLInputElement).value = UNIDADES[fv(f, "tipo")] ?? "";
      });
      $("[data-salvar]", L)?.addEventListener("click", async (e) => {
        const nome = fv(f, "nome");
        if (!nome) {
          toast("Dê um nome ao produto.");
          return;
        }

        const botao = e.target as HTMLButtonElement;
        const textoOriginal = botao.textContent;

        // Loading visual
        botao.disabled = true;
        botao.classList.add("loading");
        botao.innerHTML = '<span class="spinner"></span> Salvando…';

        try {
          const corpo = {
            nome, tipo: fv(f, "tipo") as ProdutoEntrada["tipo"], unidade: fv(f, "unidade") || "projeto", preco: numero(fv(f, "preco")),
            ativo: fv(f, "ativo") === "1", descricao: fv(f, "descricao") || null,
          };
          await gravar({
            recarregar: ["produtos"], mensagem: "Produto salvo", fechar,
            operacao: () => (p ? api.produtos.atualizar(p.id, { ...corpo, versao: p.versao }) : api.produtos.criar(corpo)),
          });
        } catch {
          botao.disabled = false;
          botao.classList.remove("loading");
          botao.innerHTML = textoOriginal || "Salvar";
        }
      });
      $("[data-excluir]", L)?.addEventListener("click", () => {
        if (p) void excluir({ recarregar: ["produtos"], mensagem: "Produto excluído", fechar, operacao: () => api.produtos.excluir(p.id) });
      });
    },
  });
}

registrarAcao("novoProduto", () => formProduto());
registrarAcao("catalogo", async (alvo) => {
  (alvo as HTMLButtonElement).disabled = true;
  if ((await tentar(() => api.produtos.catalogo())) !== null) {
    await recarregar("produtos");
    toast("Catálogo criado. Defina os preços de cada produto.");
  } else (alvo as HTMLButtonElement).disabled = false;
});
registrarAbertura("produto", (id) => {
  const p = dados.produtos.find((x) => x.id === id);
  if (p) formProduto(p);
});

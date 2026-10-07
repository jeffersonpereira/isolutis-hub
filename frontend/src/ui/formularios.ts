import { api } from "@/api/endpoints";
import { html, raw, type Safe } from "@/core/html";
import { compararTexto, hoje } from "@/core/formato";
import { dados, eu, podeEscrever, temPermissao } from "@/state/estado";
import { campo, fv, sel, type Opcao } from "./campos";
import { toast } from "./toast";
import { tentar } from "./erros";

export const botaoSalvar = (rotulo = "Salvar"): Safe => (podeEscrever() ? html`<button class="btn primary" data-salvar>${rotulo}</button>` : html``);

export const botaoExcluir = (mostrar: boolean): Safe =>
  mostrar && podeEscrever() ? html`<button class="btn danger" data-excluir>Excluir</button>` : html``;

export const espaco = raw('<span class="sp"></span>');

/** Opções de pessoas da equipe para selects de responsável. */
export const opcoesEquipe = (vazio = "Sem responsável", marcarEu = false): Opcao[] => [
  ["", vazio],
  ...dados.equipe.filter((m) => m.ativo).map((m) => [m.id, m.nome + (marcarEu && m.id === eu.id ? " (você)" : "")] as const),
];

export const opcoesClientes = (vazio = "Selecione…"): Opcao[] => [
  ["", vazio],
  ...[...dados.referenciasClientes].sort((a, b) => compararTexto(a.nome, b.nome)).map((c) => [c.id, c.nome] as const),
];

/** Campo "Cliente" com a opção "+ Novo cliente…" (cria o cliente junto com o registro). */
export function seletorCliente(valor?: string | null): Safe {
  const ops: Opcao[] = [...opcoesClientes()];
  if (podeEscrever() && temPermissao("comercial")) ops.push(["__novo", "+ Novo cliente…"]); // criar cliente é do comercial
  return campo("Cliente", html`${sel("cliente_id", ops, valor)}<input name="novo_cliente" id="f-novo_cliente" placeholder="Nome da empresa" hidden>`);
}

export function ligarNovoCliente(form: HTMLFormElement): void {
  const s = form.elements.namedItem("cliente_id") as HTMLSelectElement | null;
  const i = form.elements.namedItem("novo_cliente") as HTMLInputElement | null;
  if (!s || !i) return;
  s.addEventListener("change", () => {
    i.hidden = s.value !== "__novo";
    if (!i.hidden) i.focus();
  });
}

/** Devolve o id do cliente escolhido; se for "novo", cria antes. null = faltou algo (já avisou). */
export async function resolverCliente(form: HTMLFormElement): Promise<string | null> {
  const v = fv(form, "cliente_id");
  if (v !== "__novo") return v;
  const nome = fv(form, "novo_cliente");
  if (!nome) {
    toast("Digite o nome do novo cliente.");
    return null;
  }
  const criado = await tentar(() => api.clientes.criar({ nome }));
  if (!criado) return null;
  [dados.clientes, dados.referenciasClientes] = await Promise.all([api.clientes.listar(), api.clientes.referencias()]);
  return criado.id;
}

/** Hoje, para valores padrão de datas. */
export const dataHoje = hoje;

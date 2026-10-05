import { esc, html, raw, type Safe } from "@/core/html";

/** Auxiliares de formulário. Todos devolvem HTML já seguro para uso dentro de `html`. */
export type Opcao = readonly [valor: string | number, rotulo: string];

export const campo = (rotulo: string, conteudo: Safe | string, cheio = false): Safe =>
  html`<div class="field${cheio ? " full" : ""}"><label>${rotulo}</label>${typeof conteudo === "string" ? raw(conteudo) : conteudo}</div>`;

/** `attrs` é texto controlado pelo código (ex.: 'type="date"'), nunca dado do usuário. */
export const inp = (nome: string, valor?: string | number | null, attrs = ""): Safe =>
  raw(`<input name="${nome}" id="f-${nome}" value="${esc(valor ?? "")}" ${attrs}>`);

export const sel = (nome: string, opcoes: readonly Opcao[], valor?: string | number | null): Safe =>
  html`<select name="${nome}" id="f-${nome}">${opcoes.map(
    ([v, r]) => html`<option value="${v}"${raw(String(v) === String(valor ?? "") ? " selected" : "")}>${r}</option>`,
  )}</select>`;

export const area = (nome: string, valor?: string | null, placeholder = ""): Safe =>
  raw(`<textarea name="${nome}" id="f-${nome}" placeholder="${esc(placeholder)}">${esc(valor ?? "")}</textarea>`);

type CampoDoForm = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

/** Valor aparado de um campo do formulário ("" se não existir). */
export const fv = (form: HTMLFormElement, nome: string): string => {
  const c = form.elements.namedItem(nome) as CampoDoForm | null;
  return c?.value?.trim() ?? "";
};

export const campoDe = <T extends CampoDoForm = HTMLInputElement>(form: HTMLFormElement, nome: string): T =>
  form.elements.namedItem(nome) as T;

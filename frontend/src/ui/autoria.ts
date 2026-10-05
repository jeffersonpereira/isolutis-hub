import { quando } from "@/core/formato";
import { html, type Safe } from "@/core/html";
import { nomeDe } from "@/state/estado";

/** "Cadastrado por Ana · última alteração por Beto em 05/03 às 14:30" (nada para registro novo). */
export function linhaAutoria(reg?: {
  id?: string;
  criado_por?: string | null;
  atualizado_por?: string | null;
  atualizado_em?: string | null;
  versao?: number;
} | null): Safe | null {
  if (!reg?.id || (!reg.criado_por && !reg.atualizado_por)) return null;
  const partes: Safe[] = [];
  if (reg.criado_por) partes.push(html`Cadastrado por <b>${nomeDe(reg.criado_por)}</b>`);
  if (reg.atualizado_por && (reg.versao ?? 1) > 1) {
    partes.push(html`última alteração por <b>${nomeDe(reg.atualizado_por)}</b>${reg.atualizado_em ? " em " + quando(reg.atualizado_em) : ""}`);
  }
  if (!partes.length) return null;
  return html`<p class="sub autoria" style="margin:0">${partes.flatMap((p, i) => (i ? [" · ", p] : [p]))}</p>`;
}

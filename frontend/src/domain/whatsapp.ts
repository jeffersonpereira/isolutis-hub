import { esc, html, raw, type Safe } from "@/core/html";
import { primeiroNome } from "@/core/formato";

const ICONE =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.7.3-.2.3-.9.9-.9 2.2s.9 2.5 1 2.7c.1.2 1.8 2.8 4.4 3.9 1.6.7 2.3.8 3.1.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.3-.2-.5-.3z"/></svg>';
export const ICONE_WA = raw(ICONE);

/** Número no formato internacional (55 + DDD + número) ou "" se não for válido. */
export function numeroWa(telefone?: string | null): string {
  let d = String(telefone ?? "").replace(/\D/g, "");
  if (d.startsWith("00")) d = d.slice(2);
  if (d.length === 10 || d.length === 11) d = "55" + d;
  return d.length >= 12 ? d : "";
}

export const urlWa = (telefone: string | null | undefined, texto?: string): string =>
  "https://wa.me/" + numeroWa(telefone) + (texto ? "?text=" + encodeURIComponent(texto) : "");

export const textoContato = (contato?: string | null): string => {
  const nome = primeiroNome(contato);
  return `Olá${nome ? ", " + nome : ""}! Aqui é da iSolutis.`;
};

/** Botão do WhatsApp (link quando há número; versão desabilitada quando falta). */
export function botaoWa(
  cliente: { telefone?: string | null; contato?: string | null } | undefined,
  rotulo = "WhatsApp",
  texto?: string,
  extra = "",
): Safe {
  if (!numeroWa(cliente?.telefone)) {
    return html`<span class="btn wa ${extra}" aria-disabled="true" title="Cadastre o WhatsApp do cliente para usar este botão">${ICONE_WA}${rotulo}</span>`;
  }
  const href = urlWa(cliente?.telefone, texto ?? textoContato(cliente?.contato));
  return raw(`<a class="btn wa ${esc(extra)}" href="${esc(href)}" target="_blank" rel="noopener">${ICONE}${esc(rotulo)}</a>`);
}

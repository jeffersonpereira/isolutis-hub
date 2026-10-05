/**
 * Templates HTML seguros por padrão.
 *
 * Todo valor interpolado em `html` é escapado, a menos que já seja um `Safe` (resultado de outro `html`
 * ou de `raw`). Isso elimina a classe inteira de XSS por esquecimento de `esc()`, que era o risco do
 * sistema anterior (concatenação manual de strings).
 */
export class Safe {
  constructor(readonly valor: string) {}
  toString(): string {
    return this.valor;
  }
}

const ESCAPES: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

export function esc(v: unknown): string {
  return String(v ?? "").replace(/[&<>"']/g, (c) => ESCAPES[c] ?? c);
}

/** Marca um trecho como já seguro (use só com texto controlado pelo código, nunca com dados do usuário). */
export const raw = (s: string): Safe => new Safe(s);

function interpolar(v: unknown): string {
  if (v instanceof Safe) return v.valor;
  if (Array.isArray(v)) return v.map(interpolar).join("");
  if (v === null || v === undefined || v === false) return "";
  return esc(v);
}

export function html(partes: TemplateStringsArray, ...valores: unknown[]): Safe {
  let saida = partes[0] ?? "";
  valores.forEach((v, i) => {
    saida += interpolar(v) + (partes[i + 1] ?? "");
  });
  return new Safe(saida);
}

/** Atributo booleano: `${attr("checked", ativo)}`. */
export const attr = (nome: string, ligado: unknown): Safe => new Safe(ligado ? ` ${nome}` : "");

/**
 * Converte o que a pessoa digita (ou o que vem do banco) em número.
 *
 * Aceita "1.500,50", "1500,5", "1500.50", "1.500" (milhar), 1500.5. O sistema anterior removia todos os
 * pontos antes de converter e transformava "1500.50" em 150050; aqui o separador decimal é detectado.
 */
export function numero(valor: unknown): number {
  if (typeof valor === "number") return Number.isFinite(valor) ? valor : 0;
  let s = String(valor ?? "").trim().replace(/\s|R\$/g, "");
  if (!s) return 0;
  const negativo = s.startsWith("-");
  if (negativo) s = s.slice(1);
  if (s.includes(",")) {
    s = s.replace(/\./g, "").replace(",", ".");
  } else if (/^\d{1,3}(\.\d{3})+$/.test(s)) {
    s = s.replace(/\./g, "");
  }
  const n = Number.parseFloat(s);
  if (!Number.isFinite(n)) return 0;
  return negativo ? -n : n;
}

/** Arredonda para centavos evitando erros de ponto flutuante (ex.: 1.005). */
export const centavos = (n: number): number => Math.round((n + Number.EPSILON) * 100) / 100;

/** Valor para exibir em campo de formulário: 1500.5 -> "1500,5"; zero/vazio -> "". */
export const paraCampo = (n: number | string | null | undefined): string => {
  const v = numero(n);
  return v ? String(v).replace(".", ",") : "";
};

/**
 * Valor em reais: máscara "centavos pela direita" enquanto se digita (como em apps bancários) — os dígitos
 * digitados são sempre os centavos mais recentes, com separador de milhar e vírgula decimal.
 * A máscara é só apresentação — o valor enviado ao servidor é o número (`numero()` já interpreta o formato).
 */

import { numero } from "@/core/numero";
import { reaplicarMascaraAoFim } from "./mascara";

/** Agrupa milhar com "." e fixa duas casas decimais com ",": "150000" (dígitos) -> "1.500,00". */
function formatarCentavos(digitos: string): string {
  const d = digitos.padStart(3, "0");
  const centavos = d.slice(-2);
  const inteiro = d.slice(0, -2).replace(/^0+(?=\d)/, "").replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${inteiro},${centavos}`;
}

/** Máscara monetária parcial: descarta não dígitos e reinterpreta o restante com os 2 últimos dígitos como centavos. */
export function mascararMoeda(valor: string): string {
  const d = valor.replace(/\D/g, "").replace(/^0+(?=\d)/, "");
  if (!d) return "";
  return formatarCentavos(d);
}

/** Valor para exibir num campo monetário já mascarado: 1500.5 -> "1.500,50"; zero/vazio -> "". */
export function paraCampoMoeda(n: number | string | null | undefined): string {
  const v = numero(n);
  if (!v) return "";
  const centavos = Math.round(Math.abs(v) * 100);
  return (v < 0 ? "-" : "") + formatarCentavos(String(centavos));
}

/** Liga a máscara monetária a um campo: mascara enquanto digita, preservando a posição do cursor. */
export function ligarMascaraDeMoeda(campo: HTMLInputElement): void {
  campo.addEventListener("input", () => reaplicarMascaraAoFim(campo, mascararMoeda));
}

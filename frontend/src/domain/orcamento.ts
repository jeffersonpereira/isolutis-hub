import { numero } from "@/core/numero";
import { addDias, brl, dataBR, hoje, primeiroNome } from "@/core/formato";

/** Cálculo instantâneo dos totais enquanto a pessoa digita. O servidor recalcula e é a fonte de verdade. */
export interface ItemDigitado {
  descricao: string;
  qtd: number;
  preco_unitario: number;
  mensal: boolean;
}

export function totais(itens: readonly ItemDigitado[], desconto: number): { projeto: number; mensal: number } {
  let unico = 0;
  let mensal = 0;
  for (const i of itens) {
    const valor = Math.round(numero(i.qtd) * numero(i.preco_unitario) * 100) / 100;
    if (i.mensal) mensal += valor;
    else unico += valor;
  }
  return { projeto: Math.max(0, Math.round((unico - numero(desconto)) * 100) / 100), mensal: Math.round(mensal * 100) / 100 };
}

export interface DadosMensagem {
  /** null enquanto o orçamento não foi salvo (o número é gerado pelo servidor). */
  numero: string | null;
  data: string;
  validade: number;
  desconto: number;
  obs: string;
  itens: readonly ItemDigitado[];
}

/** Texto do orçamento para colar/enviar no WhatsApp. */
export function textoWhatsapp(o: DadosMensagem, contato: { nome?: string | null; contato?: string | null } | undefined): string {
  const t = totais(o.itens, o.desconto);
  const valido = addDias(o.data || hoje(), o.validade || 15);
  const nome = primeiroNome(contato?.contato);
  const itens = o.itens
    .filter((i) => i.descricao || numero(i.preco_unitario))
    .map(
      (i) =>
        `• ${i.descricao || "Item"}${numero(i.qtd) > 1 ? ` (${String(numero(i.qtd)).replace(".", ",")}×)` : ""}: ${brl((numero(i.qtd) || 1) * numero(i.preco_unitario))}${i.mensal ? "/mês" : ""}`,
    );
  return [
    `Olá${nome ? ", " + nome : ""}! Segue o orçamento${o.numero ? " Nº " + o.numero : ""} da iSolutis${contato?.nome ? " para " + contato.nome : ""}:`,
    "",
    ...itens,
    "",
    ...(numero(o.desconto) ? [`Desconto: −${brl(o.desconto)}`] : []),
    `*Valor do projeto: ${brl(t.projeto)}*`,
    ...(t.mensal ? [`*Manutenção mensal: ${brl(t.mensal)}/mês*`] : []),
    `Válido até ${dataBR(valido)}.`,
    ...(o.obs ? ["", o.obs] : []),
    "",
    "Fico à disposição para qualquer dúvida.",
  ].join("\n");
}

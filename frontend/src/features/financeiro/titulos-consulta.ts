/**
 * Consulta da lista de títulos (filtros, atalhos, ordem e página), sem acesso a tela ou rede: o estado mora na
 * query string (`state/consulta-url.ts`) e daqui sai o que se envia à API e os chips dos filtros ativos.
 */
import { addDias, brl, dataBR } from "@/core/formato";
import { numero } from "@/core/numero";
import { lerConsulta, type Validadores } from "@/state/consulta-url";

export const PADROES_TITULOS = {
  tipo: "todos",
  status: "todos",
  q: "",
  parceiro: "",
  plano: "",
  conta: "",
  venc_de: "",
  venc_ate: "",
  pago_de: "",
  pago_ate: "",
  vmin: "",
  vmax: "",
  origem: "todas",
  ordem: "vencimento",
  sentido: "asc",
  pag: "1",
  tam: "25",
} as const;

export type ConsultaTitulos = { -readonly [K in keyof typeof PADROES_TITULOS]: string };
type Chave = keyof ConsultaTitulos;

export const TAMANHOS_DE_PAGINA = [25, 50, 100] as const;
export const ORDENS = ["vencimento", "valor", "parceiro"] as const;

const ehData = (v: string): boolean => /^\d{4}-\d{2}-\d{2}$/.test(v);
const ehValor = (v: string): boolean => /^\d+(\.\d{1,2})?$/.test(v);
const ehId = (v: string): boolean => /^[0-9a-f-]{36}$/i.test(v);
const VALIDADORES: Validadores<Chave> = {
  tipo: (v) => ["todos", "R", "P"].includes(v),
  status: (v) => ["todos", "A", "Q", "C"].includes(v),
  parceiro: ehId,
  plano: ehId,
  conta: ehId,
  venc_de: ehData,
  venc_ate: ehData,
  pago_de: ehData,
  pago_ate: ehData,
  vmin: ehValor,
  vmax: ehValor,
  origem: (v) => ["todas", "recorrentes", "avulsos"].includes(v),
  ordem: (v) => (ORDENS as readonly string[]).includes(v),
  sentido: (v) => v === "asc" || v === "desc",
  pag: (v) => /^[1-9]\d{0,5}$/.test(v),
  tam: (v) => (TAMANHOS_DE_PAGINA as readonly number[]).includes(Number(v)),
};

export const lerConsultaTitulos = (busca: string): ConsultaTitulos => lerConsulta(PADROES_TITULOS, busca, VALIDADORES);

/** Filtros da gaveta (os que não têm botão próprio na tela). */
export const FILTROS_AVANCADOS: readonly Chave[] = ["parceiro", "plano", "conta", "venc_de", "venc_ate", "pago_de", "pago_ate", "vmin", "vmax", "origem"];

export const contarAvancados = (c: ConsultaTitulos): number => FILTROS_AVANCADOS.filter((k) => c[k] !== PADROES_TITULOS[k]).length;

/** Parâmetros de `GET /financeiro/titulos` (a exportação usa os mesmos, sem página). */
export function filtrosDaApi(c: ConsultaTitulos): Record<string, string | undefined> {
  const algum = (v: string): string | undefined => v || undefined;
  return {
    tipo: c.tipo === "todos" ? undefined : c.tipo,
    status: c.status === "todos" ? undefined : c.status,
    busca: algum(c.q),
    parceiro_id: algum(c.parceiro),
    plano_conta_id: algum(c.plano),
    conta_bancaria_id: algum(c.conta),
    de: algum(c.venc_de),
    ate: algum(c.venc_ate),
    pago_de: algum(c.pago_de),
    pago_ate: algum(c.pago_ate),
    valor_min: algum(c.vmin),
    valor_max: algum(c.vmax),
    recorrente: c.origem === "todas" ? undefined : String(c.origem === "recorrentes"),
    ordem: c.ordem,
    sentido: c.sentido,
  };
}

/** Valor digitado na gaveta ("1.500,50") no formato da URL e da API ("1500.5"); vazio ou inválido vira "". */
export function valorParaConsulta(texto: string): string {
  const n = numero(texto);
  return n > 0 ? String(Math.round(n * 100) / 100) : "";
}

// ------------------------------------------------------------------------------------------ atalhos de triagem
export type Atalho = "atrasados" | "semana";

/** Aplica um atalho: títulos abertos, com o vencimento do atalho; zera o período anterior e volta à primeira página. */
export function aplicarAtalho(c: ConsultaTitulos, atalho: Atalho, hoje: string): ConsultaTitulos {
  const periodo = atalho === "atrasados" ? { venc_de: "", venc_ate: addDias(hoje, -1) } : { venc_de: hoje, venc_ate: addDias(hoje, 6) };
  return { ...c, status: "A", ...periodo, pag: "1" };
}

/** Atalho que a consulta atual representa (para o botão aparecer pressionado), ou `null`. */
export function atalhoAtivo(c: ConsultaTitulos, hoje: string): Atalho | null {
  return (["atrasados", "semana"] as const).find((a) => {
    const esperado = aplicarAtalho(c, a, hoje);
    return c.status === "A" && c.venc_de === esperado.venc_de && c.venc_ate === esperado.venc_ate;
  }) ?? null;
}

// ------------------------------------------------------------------------------------------ chips dos filtros ativos
export interface NomesDeApoio {
  parceiro: (id: string) => string;
  plano: (id: string) => string;
  conta: (id: string) => string;
}
export interface ChipDeFiltro {
  /** Chaves da consulta que o chip limpa ao ser removido. */
  chaves: readonly Chave[];
  rotulo: string;
}

/** Um chip por filtro ativo, fora Tipo e Situação (que já têm botões próprios). Período e faixa viram um chip só. */
export function chipsDeFiltro(c: ConsultaTitulos, nomes: NomesDeApoio): ChipDeFiltro[] {
  const chips: ChipDeFiltro[] = [];
  const intervalo = (de: string, ate: string, nome: string, formato: (v: string) => string): string =>
    de && ate ? `${nome} ${formato(de)} a ${formato(ate)}` : de ? `${nome} a partir de ${formato(de)}` : `${nome} até ${formato(ate)}`;
  if (c.q) chips.push({ chaves: ["q"], rotulo: `Busca: ${c.q}` });
  if (c.parceiro) chips.push({ chaves: ["parceiro"], rotulo: `Parceiro: ${nomes.parceiro(c.parceiro)}` });
  if (c.plano) chips.push({ chaves: ["plano"], rotulo: `Conta do plano: ${nomes.plano(c.plano)}` });
  if (c.conta) chips.push({ chaves: ["conta"], rotulo: `Conta bancária: ${nomes.conta(c.conta)}` });
  if (c.venc_de || c.venc_ate) chips.push({ chaves: ["venc_de", "venc_ate"], rotulo: intervalo(c.venc_de, c.venc_ate, "Vencimento", dataBR) });
  if (c.pago_de || c.pago_ate) chips.push({ chaves: ["pago_de", "pago_ate"], rotulo: intervalo(c.pago_de, c.pago_ate, "Pagamento", dataBR) });
  if (c.vmin || c.vmax) chips.push({ chaves: ["vmin", "vmax"], rotulo: intervalo(c.vmin, c.vmax, "Valor", (v) => brl(Number(v))) });
  if (c.origem !== "todas") chips.push({ chaves: ["origem"], rotulo: c.origem === "recorrentes" ? "Só recorrentes" : "Só avulsos" });
  return chips;
}

/** Zera as chaves (voltam ao padrão) e retorna à primeira página. */
export function limparChaves(c: ConsultaTitulos, chaves: readonly Chave[]): ConsultaTitulos {
  const nova = { ...c, pag: "1" };
  for (const k of chaves) nova[k] = PADROES_TITULOS[k];
  return nova;
}

/** Última página existente para `total` títulos (ao menos 1). */
export const ultimaPagina = (total: number, tamanho: number): number => Math.max(1, Math.ceil(total / tamanho));

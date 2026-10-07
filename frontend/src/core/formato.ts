export const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
] as const;
export const MES3 = MESES.map((m) => m.slice(0, 3));

const pad = (n: number): string => String(n).padStart(2, "0");

export const brl = (n: number | string | null | undefined): string =>
  (Number(n) || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

export function brlCurto(valor: number | string | null | undefined): string {
  const n = Number(valor) || 0;
  if (Math.abs(n) >= 1e6) return "R$ " + (n / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " mi";
  if (Math.abs(n) >= 1e3) return "R$ " + (n / 1e3).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " mil";
  return brl(n);
}

/** Data de hoje no fuso local, "AAAA-MM-DD". */
export function hoje(): string {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** "AAAA-MM-DD" -> "DD/MM/AAAA" (traço quando vazio). */
export const dataBR = (s?: string | null): string => (s ? `${s.slice(8, 10)}/${s.slice(5, 7)}/${s.slice(0, 4)}` : "—");

export const mesChave = (s?: string | null): string => (s ?? "").slice(0, 7);

const partes = (iso: string): [number, number, number] => {
  const [a = 0, m = 1, d = 1] = iso.split("-").map(Number);
  return [a, m, d];
};

/** Soma meses mantendo o dia, limitado ao último dia do mês de destino (31/01 + 1 mês = 28/02). */
export function addMeses(iso: string, n: number): string {
  const [a, m, d] = partes(iso);
  const alvo = new Date(a, m - 1 + n, 1);
  const ultimo = new Date(alvo.getFullYear(), alvo.getMonth() + 1, 0).getDate();
  return `${alvo.getFullYear()}-${pad(alvo.getMonth() + 1)}-${pad(Math.min(d, ultimo))}`;
}

export function addDias(iso: string, n: number): string {
  const [a, m, d] = partes(iso);
  const t = new Date(a, m - 1, d + n);
  return `${t.getFullYear()}-${pad(t.getMonth() + 1)}-${pad(t.getDate())}`;
}

/** "2026-03-05T14:30:00Z" -> "05/03 às 11:30" (fuso local). */
export function quando(iso?: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} às ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function quandoCompleto(iso?: string | null): string {
  if (!iso) return "nunca entrou";
  const d = new Date(iso);
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} às ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export const iniciais = (nome?: string | null): string =>
  (nome ?? "?").split(/\s+/).filter(Boolean).slice(0, 2).map((p) => (p[0] ?? "").toUpperCase()).join("");

export const primeiroNome = (nome?: string | null): string => (nome ?? "").trim().split(/\s+/)[0] ?? "";

export const pluralizar = (n: number, singular: string, plural: string): string => (n === 1 ? singular : plural);

/** Minúsculas e sem acentos: "Orçamentos" casa com "orcamen". */
export const normalizarTexto = (texto: string): string => texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();

export const compararTexto = (a?: string | null, b?: string | null): number => (a ?? "").localeCompare(b ?? "", "pt");

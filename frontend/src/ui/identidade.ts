/**
 * Identidade visual da empresa ativa: logomarca acima do menu e paleta de cores da interface.
 *
 * A empresa escolhe duas cores (primária e destaque); daqui saem os demais tons dos temas claro e escuro,
 * sempre com contraste mínimo para leitura (uma cor clara demais é escurecida onde vira texto ou fundo do
 * menu). A última identidade de cada empresa fica em `localStorage` para ser aplicada antes da resposta do
 * servidor, sem piscar a logo e as cores padrão. Armazenamento indisponível não impede o funcionamento.
 */
import type { components } from "@/api/schema";

export type Paleta = components["schemas"]["Paleta"];

export interface Identidade {
  logo: string | null;
  paleta: Paleta | null;
}

/** Paleta padrão do Hub (a mesma de `tokens.css`). */
export const PALETA_PADRAO: Paleta = { primaria: "#0B2D3B", destaque: "#4F6B8F" };

export const PALETAS_SUGERIDAS: ReadonlyArray<{ nome: string; paleta: Paleta }> = [
  { nome: "AIME Tech (padrão)", paleta: PALETA_PADRAO },
  { nome: "Oceano", paleta: { primaria: "#0b2e5c", destaque: "#1e88e5" } },
  { nome: "Floresta", paleta: { primaria: "#1b4332", destaque: "#40916c" } },
  { nome: "Vinho", paleta: { primaria: "#4a1526", destaque: "#c0485e" } },
  { nome: "Grafite", paleta: { primaria: "#2b2d42", destaque: "#e07a3f" } },
  { nome: "Ametista", paleta: { primaria: "#33184f", destaque: "#8e5bd0" } },
  { nome: "Terra", paleta: { primaria: "#3d2c1e", destaque: "#c98a2e" } },
];

// ---------------------------------------------------------------------------------------------- cores
type Rgb = [number, number, number];

const COR_HEX = /^#[0-9a-f]{6}$/i;
export const corValida = (cor: string): boolean => COR_HEX.test(cor);

function rgb(hex: string): Rgb {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

const hex = (c: Rgb): string => "#" + c.map((v) => Math.round(Math.min(255, Math.max(0, v))).toString(16).padStart(2, "0")).join("");

/** Mistura `a` com `b`: peso 0 devolve `a`, 1 devolve `b`. */
export function misturar(a: string, b: string, peso: number): string {
  const x = rgb(a);
  const y = rgb(b);
  return hex([0, 1, 2].map((i) => x[i]! + (y[i]! - x[i]!) * peso) as Rgb);
}

/** Luminância relativa (WCAG 2). */
export function luminancia(cor: string): number {
  const [r, g, b] = rgb(cor).map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  }) as Rgb;
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contraste(a: string, b: string): number {
  const [l1, l2] = [luminancia(a), luminancia(b)].sort((x, y) => y - x) as [number, number];
  return (l1 + 0.05) / (l2 + 0.05);
}

/** Escurece (ou clareia, se `fundo` for escuro) `cor` aos poucos até ter o contraste mínimo com `fundo`. */
export function comContraste(cor: string, fundo: string, minimo: number): string {
  const alvo = luminancia(fundo) > 0.5 ? "#000000" : "#ffffff";
  let atual = cor;
  for (let passo = 1; passo <= 20 && contraste(atual, fundo) < minimo; passo++) atual = misturar(cor, alvo, passo / 20);
  return atual;
}

/** Texto legível sobre `fundo`: branco ou o tom escuro da interface. */
export const textoSobre = (fundo: string, escuro = "#0d1520"): string => (contraste(fundo, "#ffffff") >= contraste(fundo, escuro) ? "#ffffff" : escuro);

/** Tokens CSS (`tokens.css`) de cada tema derivados das duas cores escolhidas. */
export function tokensDaPaleta(p: Paleta): { claro: Record<string, string>; escuro: Record<string, string> } {
  const BRANCO = "#ffffff";
  const FUNDO_ESCURO = "#151e2f";
  // Primária: usada como texto/fundo de botão no tema claro, precisa de contraste com o branco.
  const primaria = comContraste(p.primaria, BRANCO, 4.5);
  // O menu lateral é escuro nos dois temas: o fundo dele é a primária bem escurecida.
  const lateral = comContraste(misturar(primaria, "#000000", 0.42), "#c6d0de", 7);
  const destaque = p.destaque;
  const destaqueEscuro = comContraste(misturar(destaque, BRANCO, 0.2), FUNDO_ESCURO, 4.5);
  return {
    claro: {
      "--navy": primaria,
      "--navy-deep": lateral,
      "--accent": primaria,
      "--accent-ink": textoSobre(primaria),
      "--teal": destaque,
      "--teal-mid": comContraste(misturar(destaque, "#000000", 0.18), BRANCO, 3),
      "--teal-pale": misturar(destaque, BRANCO, 0.84),
      "--teal-texto": comContraste(destaque, BRANCO, 4.5),
      "--bar-a": primaria,
      "--bar-b": misturar(destaque, BRANCO, 0.62),
      "--side-bg": lateral,
      "--side-ativo": misturar(lateral, BRANCO, 0.12),
      "--side-linha": misturar(lateral, BRANCO, 0.07),
    },
    escuro: {
      "--accent": destaque,
      "--accent-ink": textoSobre(destaque),
      "--teal-mid": destaqueEscuro,
      "--teal-pale": misturar(destaque, "#0d1520", 0.74),
      "--teal-texto": destaqueEscuro,
      "--bar-a": destaque,
      "--bar-b": misturar(primaria, BRANCO, 0.22),
    },
  };
}

const bloco = (seletor: string, tokens: Record<string, string>): string =>
  `${seletor}{${Object.entries(tokens).map(([k, v]) => `${k}:${v}`).join(";")}}`;

/** CSS que sobrepõe os tokens padrão (mesma especificidade de `tokens.css`, vem depois dele). */
export function cssDaPaleta(p: Paleta): string {
  const t = tokensDaPaleta(p);
  return bloco(":root", t.claro) + bloco(':root[data-theme="dark"]', { ...t.claro, ...t.escuro });
}

// ---------------------------------------------------------------------------------------------- aplicação
const ID_ESTILO = "paleta-empresa";

/** Aplica a paleta ao documento (null volta à padrão). Também serve de pré-visualização na tela de cores. */
export function aplicarPaleta(p: Paleta | null, doc: Document = document): void {
  let estilo = doc.getElementById(ID_ESTILO);
  if (!p || (p.primaria === PALETA_PADRAO.primaria && p.destaque === PALETA_PADRAO.destaque)) {
    estilo?.remove();
    return;
  }
  if (!estilo) {
    estilo = doc.createElement("style");
    estilo.id = ID_ESTILO;
    doc.head.appendChild(estilo);
  }
  estilo.textContent = cssDaPaleta(p);
}

const LOGO_PADRAO = "/aime-horizontal-reverso.svg";
const MARCA_PADRAO = "/aime-simbolo-reverso.svg";

/** Troca a logo acima do menu (e o ícone do menu recolhido) pela da empresa; null volta à logo padrão. */
export function aplicarLogo(logo: string | null, nomeEmpresa = "", doc: Document = document): void {
  const caixa = doc.getElementById("logoSide");
  if (!caixa) return;
  const [grande, pequena] = Array.from(caixa.querySelectorAll("img"));
  caixa.classList.toggle("logo-propria", !!logo);
  if (grande) {
    grande.src = logo ?? LOGO_PADRAO;
    grande.alt = logo ? nomeEmpresa || "Logomarca da empresa" : "AIME Tech";
  }
  if (pequena) {
    pequena.src = logo ?? MARCA_PADRAO;
    pequena.alt = grande?.alt ?? "AIME Tech";
  }
}

export function aplicarIdentidade(id: Identidade, nomeEmpresa = ""): void {
  aplicarLogo(id.logo, nomeEmpresa);
  aplicarPaleta(id.paleta);
}

// ---------------------------------------------------------------------------------------------- memória local
const chave = (empresaId: string): string => `hub.identidade.${empresaId}`;

export function lembrarIdentidade(empresaId: string, id: Identidade): void {
  try {
    localStorage.setItem(chave(empresaId), JSON.stringify(id));
  } catch {
    /* sem armazenamento (ou logo grande demais para a cota): só não aplica antes do servidor responder */
  }
}

export function identidadeLembrada(empresaId: string): Identidade | null {
  try {
    const salvo = JSON.parse(localStorage.getItem(chave(empresaId)) ?? "null") as Partial<Identidade> | null;
    if (!salvo || typeof salvo !== "object") return null;
    const paleta = salvo.paleta && corValida(salvo.paleta.primaria) && corValida(salvo.paleta.destaque) ? salvo.paleta : null;
    const logo = typeof salvo.logo === "string" && salvo.logo.startsWith("data:image/") ? salvo.logo : null;
    return { logo, paleta };
  } catch {
    return null;
  }
}

/** Ao sair da sessão: nenhuma identidade de empresa fica para a próxima pessoa no mesmo navegador. */
export function esquecerIdentidades(): void {
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith("hub.identidade."))
      .forEach((k) => localStorage.removeItem(k));
  } catch {
    /* sem armazenamento: nada a limpar */
  }
}

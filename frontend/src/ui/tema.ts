/**
 * Tema da interface: Sistema (padrão), Claro ou Escuro.
 *
 * A escolha fica em `localStorage` (`hub.tema`). O mesmo cálculo roda num script embutido no `<head>` do
 * `index.html`, antes da primeira pintura, para não piscar o tema errado; aqui ficam a troca em tempo de uso
 * e o acompanhamento do sistema operacional. Armazenamento indisponível não impede o funcionamento.
 */
export type PreferenciaTema = "sistema" | "claro" | "escuro";
export type TemaAplicado = "light" | "dark";

export const CHAVE_TEMA = "hub.tema";
const CONSULTA_ESCURO = "(prefers-color-scheme: dark)";

interface Armazenamento {
  getItem(chave: string): string | null;
  setItem(chave: string, valor: string): void;
}

const preferenciaValida = (v: string | null): v is PreferenciaTema => v === "sistema" || v === "claro" || v === "escuro";

/** Preferência salva; qualquer valor desconhecido ou erro de leitura vale "sistema". */
export function lerPreferencia(armazenamento: Armazenamento | null = seguro()): PreferenciaTema {
  try {
    const salvo = armazenamento?.getItem(CHAVE_TEMA) ?? null;
    return preferenciaValida(salvo) ? salvo : "sistema";
  } catch {
    return "sistema";
  }
}

export function salvarPreferencia(pref: PreferenciaTema, armazenamento: Armazenamento | null = seguro()): void {
  try {
    armazenamento?.setItem(CHAVE_TEMA, pref);
  } catch {
    /* modo privado ou armazenamento bloqueado: vale só até recarregar */
  }
}

/** Tema efetivamente usado, dado o que o usuário escolheu e o que o sistema operacional prefere. */
export const resolverTema = (pref: PreferenciaTema, sistemaEscuro: boolean): TemaAplicado =>
  pref === "escuro" || (pref === "sistema" && sistemaEscuro) ? "dark" : "light";

function seguro(): Armazenamento | null {
  try {
    return typeof localStorage === "undefined" ? null : localStorage;
  } catch {
    return null;
  }
}

const sistemaEscuro = (): boolean => typeof matchMedia === "function" && matchMedia(CONSULTA_ESCURO).matches;

/** Aplica a preferência ao documento e devolve o tema resultante. */
export function aplicarTema(pref: PreferenciaTema, doc: Document = document): TemaAplicado {
  const tema = resolverTema(pref, sistemaEscuro());
  doc.documentElement.setAttribute("data-theme", tema);
  return tema;
}

/** Salva e aplica a escolha do usuário. */
export function definirTema(pref: PreferenciaTema): TemaAplicado {
  salvarPreferencia(pref);
  return aplicarTema(pref);
}

/**
 * Aplica a preferência salva e, enquanto ela for "sistema", acompanha mudanças do sistema operacional.
 * `aoMudar` recebe o tema aplicado (para a interface atualizar o ícone do botão de tema).
 */
export function iniciarTema(aoMudar: (pref: PreferenciaTema, tema: TemaAplicado) => void = () => {}): void {
  aoMudar(lerPreferencia(), aplicarTema(lerPreferencia()));
  if (typeof matchMedia !== "function") return;
  matchMedia(CONSULTA_ESCURO).addEventListener("change", () => {
    const pref = lerPreferencia();
    if (pref === "sistema") aoMudar(pref, aplicarTema(pref));
  });
}

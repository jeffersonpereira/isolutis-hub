export const $ = <T extends Element = HTMLElement>(seletor: string, raiz: ParentNode = document): T | null =>
  raiz.querySelector<T>(seletor);

export const $$ = <T extends Element = HTMLElement>(seletor: string, raiz: ParentNode = document): T[] =>
  [...raiz.querySelectorAll<T>(seletor)];

/** Versão de `$` que falha alto quando o elemento é obrigatório para a tela. */
export function obrigatorio<T extends Element = HTMLElement>(seletor: string, raiz: ParentNode = document): T {
  const el = raiz.querySelector<T>(seletor);
  if (!el) throw new Error(`Elemento não encontrado: ${seletor}`);
  return el;
}

/** Delegação de eventos: um único ouvinte na raiz, resolvendo o alvo por seletor. */
export function delegar<K extends keyof DocumentEventMap>(
  raiz: Document | HTMLElement,
  tipo: K,
  seletor: string,
  tratador: (alvo: HTMLElement, evento: DocumentEventMap[K]) => void,
): void {
  raiz.addEventListener(tipo, (evento) => {
    const alvo = (evento.target as Element | null)?.closest<HTMLElement>(seletor);
    if (alvo && raiz.contains(alvo)) tratador(alvo, evento as DocumentEventMap[K]);
  });
}

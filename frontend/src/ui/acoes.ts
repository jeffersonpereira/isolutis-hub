/**
 * Registro de ações disparadas por `data-act="nome"`.
 *
 * Cada funcionalidade registra as suas; um único ouvinte global despacha. Assim a vista só declara
 * o que o botão faz (`data-act`) e o comportamento fica no módulo da funcionalidade.
 */
type Acao = (alvo: HTMLElement) => void | Promise<void>;
const acoes = new Map<string, Acao>();

export function registrarAcao(nome: string, fn: Acao): void {
  acoes.set(nome, fn);
}

export async function despachar(nome: string, alvo: HTMLElement): Promise<boolean> {
  const fn = acoes.get(nome);
  if (!fn) return false;
  await fn(alvo);
  return true;
}

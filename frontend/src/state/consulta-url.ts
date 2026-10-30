/**
 * Estado de uma listagem (filtros, ordem e página) na query string da URL.
 *
 * Cada tela declara os seus `padroes`; só o que difere do padrão vai para o endereço, e valores inválidos
 * voltam ao padrão. As funções de leitura e de texto não tocam em `location`, para poderem ser testadas à parte.
 */
export type Padroes<K extends string> = Readonly<Record<K, string>>;
export type Validadores<K extends string> = Partial<Record<K, (valor: string) => boolean>>;

/** Lê os valores de `busca` ("?a=b"); chave ausente ou inválida fica com o padrão. */
export function lerConsulta<K extends string>(padroes: Padroes<K>, busca: string, validadores: Validadores<K> = {}): Record<K, string> {
  const params = new URLSearchParams(busca);
  const saida = { ...padroes } as Record<K, string>;
  for (const chave of Object.keys(padroes) as K[]) {
    const valor = params.get(chave)?.trim();
    if (valor === undefined || valor === "") continue;
    if (validadores[chave]?.(valor) === false) continue;
    saida[chave] = valor;
  }
  return saida;
}

/** Texto da query string ("?a=b" ou "" quando tudo é padrão), na ordem em que os padrões foram declarados. */
export function consultaParaTexto<K extends string>(padroes: Padroes<K>, valores: Readonly<Record<K, string>>): string {
  const params = new URLSearchParams();
  for (const chave of Object.keys(padroes) as K[]) {
    if (valores[chave] !== padroes[chave]) params.set(chave, valores[chave]);
  }
  const texto = params.toString();
  return texto ? `?${texto}` : "";
}

/** Grava a consulta no endereço da tela atual. `replace` não empilha histórico; `push` cria uma entrada (troca de página). */
export function gravarConsulta<K extends string>(padroes: Padroes<K>, valores: Readonly<Record<K, string>>, modo: "push" | "replace"): void {
  const destino = location.pathname + consultaParaTexto(padroes, valores);
  if (destino === location.pathname + location.search) return;
  if (modo === "push") history.pushState(null, "", destino);
  else history.replaceState(null, "", destino);
}

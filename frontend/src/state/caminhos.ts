/**
 * Caminhos (URLs) da aplicação, sem dependência do resto do código para poderem ser testados à parte.
 *
 *   /                 → a última tela usada
 *   /<tela>           → uma tela (id de `registrarVista`, ex.: /clientes, /fin-titulos)
 *   /<tela>/novo      → formulário em página de um novo registro
 *   /<tela>/<id>      → formulário em página de um registro existente
 *
 * `/login`, `/login/2fa`, `/convite/<token>`, `/assets` e `/api` são reservados: não passam pelo roteador de telas.
 */
export type RotaResolvida =
  | { tipo: "raiz" }
  | { tipo: "tela"; vista: string }
  | { tipo: "novo"; vista: string }
  | { tipo: "registro"; vista: string; id: string }
  | { tipo: "reservada" }
  | { tipo: "desconhecida" };

const RESERVADAS = ["login", "convite", "assets", "api"];

export const caminhoDaTela = (vista: string): string => `/${vista}`;
export const caminhoNovo = (vista: string): string => `/${vista}/novo`;
export const caminhoDoRegistro = (vista: string, id: string): string => `/${vista}/${encodeURIComponent(id)}`;

export function resolverCaminho(caminho: string, telas: ReadonlySet<string>): RotaResolvida {
  const limpo = (caminho.split(/[?#]/)[0] ?? "").replace(/\/+$/, "");
  if (limpo === "") return { tipo: "raiz" };
  const partes = limpo.split("/").slice(1);
  const primeira = partes[0] ?? "";
  if (RESERVADAS.includes(primeira)) return { tipo: "reservada" };
  if (!telas.has(primeira) || partes.length > 2 || partes.some((p) => p === "")) return { tipo: "desconhecida" };
  if (partes.length === 1) return { tipo: "tela", vista: primeira };
  const segundo = partes[1] ?? "";
  if (segundo === "novo") return { tipo: "novo", vista: primeira };
  try {
    return { tipo: "registro", vista: primeira, id: decodeURIComponent(segundo) };
  } catch {
    return { tipo: "desconhecida" };
  }
}

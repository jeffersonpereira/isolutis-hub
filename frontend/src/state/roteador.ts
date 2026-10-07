/**
 * Roteador por URL (History API). Faz a ponte entre o endereço do navegador e as telas registradas:
 * rota inicial ao abrir, Voltar e Avançar, e as rotas de registro (`/<tela>/novo`, `/<tela>/<id>`) das telas
 * que usam formulário em página. Os caminhos em si estão em `caminhos.ts`.
 */
import { caminhoDaTela, resolverCaminho, type RotaResolvida } from "./caminhos";
import { abaSalva, atualizarUrl, caminhoAtual, ir, podeSair, vistasVisiveis } from "./nucleo";

export interface RotaDeRegistro {
  /** Abre o formulário de um novo registro. */
  novo: () => void;
  /** Abre o registro; se ele não existir, a própria tela mostra "Registro não encontrado". */
  abrir: (id: string) => void;
}

const rotasDeRegistro = new Map<string, RotaDeRegistro>();
export const registrarRotaDeRegistro = (vista: string, rota: RotaDeRegistro): void => void rotasDeRegistro.set(vista, rota);

const telasVisiveis = (): Set<string> => new Set(vistasVisiveis().map((v) => v.id));

export interface RotaInicial {
  vista: string;
  /** Caminho a gravar no lugar do atual (raiz, rota desconhecida ou sem permissão), ou `null` se já está certo. */
  corrigir: string | null;
  /** Registro a abrir depois que os dados carregarem. */
  registro: RotaResolvida | null;
}

/** Tela que o endereço pede ao abrir a aplicação. A raiz reabre a última tela; endereço explícito prevalece. */
export function resolverRotaInicial(caminho: string = location.pathname): RotaInicial {
  const telas = telasVisiveis();
  const rota = resolverCaminho(caminho, telas);
  switch (rota.tipo) {
    case "tela":
      return { vista: rota.vista, corrigir: null, registro: null };
    case "novo":
    case "registro":
      return { vista: rota.vista, corrigir: null, registro: rota };
    case "raiz":
    case "reservada": {
      const salva = abaSalva();
      const vista = telas.has(salva) ? salva : "painel";
      return { vista, corrigir: caminhoDaTela(vista), registro: null };
    }
    default:
      return { vista: "painel", corrigir: caminhoDaTela("painel"), registro: null };
  }
}

/** Abre o formulário de registro que a rota pede (depois que a tela e os dados já estão carregados). */
export function aplicarRegistroDaRota(rota: RotaResolvida | null): void {
  if (rota?.tipo === "novo") rotasDeRegistro.get(rota.vista)?.novo();
  else if (rota?.tipo === "registro") rotasDeRegistro.get(rota.vista)?.abrir(rota.id);
}

async function aoVoltarOuAvancar(): Promise<void> {
  const rota = resolverCaminho(location.pathname, telasVisiveis());
  if (rota.tipo === "reservada") return;
  // Alterações pendentes: se o usuário optar por ficar, devolve o endereço de antes.
  if (!(await podeSair())) {
    atualizarUrl(caminhoAtual(), "push");
    return;
  }
  if (rota.tipo === "raiz" || rota.tipo === "desconhecida") {
    await ir(rota.tipo === "raiz" ? abaSalva() : "painel", { historico: "replace", semGuarda: true });
    return;
  }
  await ir(rota.vista, { historico: "nenhum", semGuarda: true });
  aplicarRegistroDaRota(rota);
}

export function iniciarRoteador(): void {
  window.addEventListener("popstate", () => void aoVoltarOuAvancar());
}

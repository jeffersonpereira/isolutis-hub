/** Cliente HTTP único da aplicação: token, formato de erro da API e download de arquivos. */
const BASE = `${import.meta.env.VITE_API_URL ?? ""}/api/v1`;
const CHAVE_TOKEN = "hub.token";
const CHAVE_EMPRESA = "hub.empresa";

export class ErroApi extends Error {
  constructor(
    readonly status: number,
    readonly codigo: string,
    mensagem: string,
    readonly detalhes?: unknown,
  ) {
    super(mensagem);
  }
}

type Consulta = Record<string, string | number | boolean | null | undefined>;

let token: string | null = null;
/** Empresa ativa DESTA aba (sessionStorage). A última usada (localStorage) é só sugestão na tela de escolha. */
let empresa: string | null = null;
let ultimaEmpresa: string | null = null;
try {
  token = localStorage.getItem(CHAVE_TOKEN);
  ultimaEmpresa = localStorage.getItem(CHAVE_EMPRESA);
  empresa = sessionStorage.getItem(CHAVE_EMPRESA);
} catch {
  /* armazenamento indisponível (modo privado): a sessão vale só até recarregar */
}
const ouvintesSessaoExpirada: Array<() => void> = [];
const ouvintesEmpresaPerdida: Array<() => void> = [];

export const sessaoToken = {
  definir(valor: string | null): void {
    token = valor;
    try {
      if (valor) localStorage.setItem(CHAVE_TOKEN, valor);
      else localStorage.removeItem(CHAVE_TOKEN);
    } catch {
      /* ver acima */
    }
  },
  obter: (): string | null => token,
  empresa: (): string | null => empresa,
  ultimaEmpresa: (): string | null => ultimaEmpresa,
  /** Escolhe a empresa desta aba e a lembra como a última usada. */
  definirEmpresa(valor: string): void {
    empresa = valor;
    ultimaEmpresa = valor;
    try {
      sessionStorage.setItem(CHAVE_EMPRESA, valor);
      localStorage.setItem(CHAVE_EMPRESA, valor);
    } catch { /* armazenamento indisponível */ }
  },
  /** Descarta só a empresa desta aba (troca de empresa ou acesso perdido); a última usada continua como sugestão. */
  esquecerEmpresaDaAba(): void {
    empresa = null;
    try {
      sessionStorage.removeItem(CHAVE_EMPRESA);
    } catch { /* armazenamento indisponível */ }
  },
  /** Ao sair: nada da escolha de um usuário pode sobrar para o próximo no mesmo navegador. */
  limparEmpresas(): void {
    empresa = null;
    ultimaEmpresa = null;
    try {
      sessionStorage.removeItem(CHAVE_EMPRESA);
      localStorage.removeItem(CHAVE_EMPRESA);
    } catch { /* armazenamento indisponível */ }
  },
  /** Chamado quando o servidor recusa a empresa ativa por falta de acesso (ela já foi descartada da aba). */
  aoPerderEmpresa(fn: () => void): void {
    ouvintesEmpresaPerdida.push(fn);
  },
  aoExpirar(fn: () => void): void {
    ouvintesSessaoExpirada.push(fn);
  },
};

function montarUrl(caminho: string, consulta?: Consulta): string {
  const url = new URL(BASE + caminho, window.location.origin);
  for (const [k, v] of Object.entries(consulta ?? {})) {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
  }
  return BASE.startsWith("http") ? url.toString() : url.pathname + url.search;
}

async function converterErro(resposta: Response): Promise<ErroApi> {
  let codigo = "http";
  let mensagem = "Não foi possível concluir a operação agora. Verifique a conexão e tente de novo.";
  let detalhes: unknown;
  try {
    const corpo = (await resposta.json()) as { erro?: { codigo: string; mensagem: string; detalhes?: unknown } };
    if (corpo.erro) {
      codigo = corpo.erro.codigo;
      mensagem = corpo.erro.mensagem;
      detalhes = corpo.erro.detalhes;
    }
  } catch {
    /* resposta sem JSON: mantém a mensagem padrão */
  }
  return new ErroApi(resposta.status, codigo, mensagem, detalhes);
}

async function enviar(metodo: string, caminho: string, opcoes: { corpo?: unknown; consulta?: Consulta } = {}): Promise<Response> {
  const cabecalhos: Record<string, string> = { Accept: "application/json" };
  if (token) cabecalhos.Authorization = `Bearer ${token}`;
  if (empresa) cabecalhos["X-Empresa-ID"] = empresa;
  if (opcoes.corpo !== undefined) cabecalhos["Content-Type"] = "application/json";
  let resposta: Response;
  try {
    resposta = await fetch(montarUrl(caminho, opcoes.consulta), {
      method: metodo,
      headers: cabecalhos,
      body: opcoes.corpo === undefined ? undefined : JSON.stringify(opcoes.corpo),
    });
  } catch {
    throw new ErroApi(0, "rede", "Sem conexão com o servidor. Verifique a internet e tente de novo.");
  }
  if (!resposta.ok) {
    const erro = await converterErro(resposta);
    if (erro.status === 401 && token && caminho !== "/auth/login") {
      sessaoToken.definir(null);
      ouvintesSessaoExpirada.forEach((fn) => fn());
    }
    if (erro.status === 403 && erro.codigo === "empresa_inacessivel" && empresa) {
      sessaoToken.esquecerEmpresaDaAba();
      ouvintesEmpresaPerdida.forEach((fn) => fn());
    }
    throw erro;
  }
  return resposta;
}

async function json<T>(metodo: string, caminho: string, opcoes?: { corpo?: unknown; consulta?: Consulta }): Promise<T> {
  const resposta = await enviar(metodo, caminho, opcoes);
  return resposta.status === 204 ? (undefined as T) : ((await resposta.json()) as T);
}

export const http = {
  get: <T>(caminho: string, consulta?: Consulta) => json<T>("GET", caminho, { consulta }),
  post: <T>(caminho: string, corpo?: unknown) => json<T>("POST", caminho, { corpo: corpo ?? {} }),
  put: <T>(caminho: string, corpo: unknown) => json<T>("PUT", caminho, { corpo }),
  patch: <T>(caminho: string, corpo: unknown) => json<T>("PATCH", caminho, { corpo }),
  delete: (caminho: string) => json<void>("DELETE", caminho),

  /** Baixa um arquivo gerado pelo servidor (com autenticação) e entrega ao navegador. */
  async baixar(caminho: string, consulta?: Consulta): Promise<void> {
    const resposta = await enviar("GET", caminho, { consulta });
    const disposicao = resposta.headers.get("Content-Disposition") ?? "";
    const nome = /filename\*=UTF-8''([^;]+)/i.exec(disposicao)?.[1];
    const blob = await resposta.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = nome ? decodeURIComponent(nome) : "arquivo";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  },
};

export function urlWebSocket(): string {
  const base = import.meta.env.VITE_API_URL
    ? String(import.meta.env.VITE_API_URL).replace(/^http/, "ws")
    : window.location.origin.replace(/^http/, "ws");
  return `${base}/api/v1/ws`;
}

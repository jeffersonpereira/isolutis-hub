/**
 * Registro que a pessoa está editando agora, seja numa gaveta ou num formulário em página.
 *
 * Três módulos dependem disto: o aviso de edição concorrente (`conflito.ts`), a gravação (`gravacao.ts`, que
 * registra a versão gravada pela própria sessão para não acusar conflito consigo mesma) e a presença
 * "editando…" mostrada aos colegas. Gaveta e formulário em página usam o mesmo estado e o mesmo contrato.
 */
export interface RegistroAberto {
  recurso: string;
  id: string;
  versao: number;
  /** Versão que esta própria sessão acabou de gravar (para não acusar conflito consigo mesma). */
  minhaVersao: number | null;
  excluidoPorMim: boolean;
}

export let registroAberto: RegistroAberto | null = null;

type AoMudar = (titulo: string | null, editando: boolean) => void;
let aoMudar: AoMudar = () => {};
/** Quem precisa saber quando alguém abre ou fecha um registro (a presença "editando…"). */
export const observarRegistro = (fn: AoMudar): void => {
  aoMudar = fn;
};

/** O que estava aberto antes, para restaurar quando uma gaveta se fecha por cima de um formulário em página. */
export interface RegistroAnterior {
  titulo: string | null;
  registro: RegistroAberto | null;
}

let tituloAtual: string | null = null;

export function abrirRegistro(titulo: string, registro?: { recurso: string; id: string; versao: number } | null): RegistroAnterior {
  const anterior: RegistroAnterior = { titulo: tituloAtual, registro: registroAberto };
  registroAberto = registro ? { ...registro, minhaVersao: null, excluidoPorMim: false } : null;
  tituloAtual = titulo;
  aoMudar(titulo, !!registro);
  return anterior;
}

export function fecharRegistro(anterior?: RegistroAnterior): void {
  registroAberto = anterior?.registro ?? null;
  tituloAtual = anterior?.titulo ?? null;
  aoMudar(tituloAtual, !!registroAberto);
}

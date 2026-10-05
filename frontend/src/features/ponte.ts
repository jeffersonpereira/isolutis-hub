/**
 * Ponte entre funcionalidades: permite que uma tela abra o formulário de outra sem importá-la
 * (evita dependências circulares, p.ex. negócio ↔ orçamento ↔ projeto ↔ faturamento).
 */
import type { Negocio, OrcamentoEntrada, Projeto, ProjetoEntrada } from "@/api/tipos";

export interface VendaFechada {
  cliente_id: string;
  titulo: string;
  unico: number;
  mensal: number;
  negocio_id?: string | null;
  orcamento_id?: string | null;
}

interface Formularios {
  negocio: (inicial?: Partial<Negocio> & { cliente_id?: string }) => void;
  orcamento: (inicial?: Partial<OrcamentoEntrada>) => void;
  projeto: (existente?: Projeto, inicial?: Partial<ProjetoEntrada>) => void;
  /** Abre o projeto novo já preenchido com os dados do negócio ganho. */
  projetoDoNegocio: (negocioId: string) => void;
  faturamento: (venda: VendaFechada) => void;
}

const formularios: Partial<Formularios> = {};

export function registrarFormulario<K extends keyof Formularios>(nome: K, fn: Formularios[K]): void {
  formularios[nome] = fn;
}

export function abrirFormulario<K extends keyof Formularios>(nome: K, ...args: Parameters<Formularios[K]>): void {
  const fn = formularios[nome] as ((...a: Parameters<Formularios[K]>) => void) | undefined;
  fn?.(...args);
}

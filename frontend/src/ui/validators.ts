/** Sistema de validação simples e reutilizável. */

export type ErroValidacao = Record<string, string>;

export type Regra<T> = (valor: T) => string | null;

export interface Schema<T> {
  parse(dados: unknown): { sucesso: true; dados: T } | { sucesso: false; erros: ErroValidacao };
}

/** Cria uma função que valida um campo contra múltiplas regras. */
export function campo<T>(
  nome: string,
  regras: Regra<T>[],
): { validar: (valor: T) => string | null; nome: string } {
  return {
    nome,
    validar: (valor: T) => {
      for (const regra of regras) {
        const erro = regra(valor);
        if (erro) return erro;
      }
      return null;
    },
  };
}

/** Schema builder para validação de objetos. */
export function schema<T extends Record<string, unknown>>(
  campos: Record<keyof T, { validar: (valor: unknown) => string | null }>,
): Schema<T> {
  return {
    parse(dados: unknown) {
      const erros: ErroValidacao = {};
      const resultado: Partial<T> = {};

      if (typeof dados !== "object" || dados === null) {
        return { sucesso: false, erros: { _global: "Dados inválidos" } };
      }

      for (const [chave, { validar }] of Object.entries(campos)) {
        const valor = (dados as Record<string, unknown>)[chave];
        const erro = validar(valor);
        if (erro) {
          erros[chave] = erro;
        } else {
          resultado[chave as keyof T] = valor as T[keyof T];
        }
      }

      return Object.keys(erros).length === 0
        ? { sucesso: true, dados: resultado as T }
        : { sucesso: false, erros };
    },
  };
}

// Regras comuns
export const regras = {
  obrigatorio: (nome = "Este campo"): Regra<string | null | undefined> => (valor) =>
    valor ? null : `${nome} é obrigatório.`,

  email: (): Regra<string> => (valor) =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor) ? null : "E-mail inválido.",

  minLength: (min: number, nome = "Este campo"): Regra<string> => (valor) =>
    valor.length >= min ? null : `${nome} deve ter pelo menos ${min} caracteres.`,

  maxLength: (max: number, nome = "Este campo"): Regra<string> => (valor) =>
    valor.length <= max ? null : `${nome} pode ter no máximo ${max} caracteres.`,

  numero: (nome = "Este campo"): Regra<string> => (valor) => {
    const n = Number(valor);
    return !isNaN(n) && n > 0 ? null : `${nome} deve ser um número válido.`;
  },

  dataFutura: (): Regra<string> => (valor) => {
    const data = new Date(valor);
    return data > new Date() ? null : "A data deve ser no futuro.";
  },
};

// @vitest-environment jsdom
import { describe, expect, it } from "vitest";
import { ligarMascaraDeMoeda, mascararMoeda, paraCampoMoeda } from "./moeda";

describe("mascararMoeda", () => {
  it("dígito único vira centavos", () => {
    expect(mascararMoeda("1")).toBe("0,01");
    expect(mascararMoeda("5")).toBe("0,05");
  });

  it("agrupa milhar ao crescer", () => {
    expect(mascararMoeda("150000")).toBe("1.500,00");
    expect(mascararMoeda("1500000")).toBe("15.000,00");
  });

  it("apagar dígitos reduz o valor", () => {
    expect(mascararMoeda("1.500,0")).toBe("150,00");
  });

  it("colar com R$ e espaços descarta o que não é dígito", () => {
    expect(mascararMoeda("R$ 1.500,00")).toBe("1.500,00");
    expect(mascararMoeda("R$ 1.500,5")).toBe("150,05");
  });

  it("vazio ou só zeros", () => {
    expect(mascararMoeda("")).toBe("");
    expect(mascararMoeda("0")).toBe("0,00");
  });
});

describe("paraCampoMoeda", () => {
  it("número vira texto mascarado", () => {
    expect(paraCampoMoeda(1500.5)).toBe("1.500,50");
    expect(paraCampoMoeda("1500.5")).toBe("1.500,50");
    expect(paraCampoMoeda(1500000)).toBe("1.500.000,00");
  });

  it("zero ou vazio vira string vazia", () => {
    expect(paraCampoMoeda(0)).toBe("");
    expect(paraCampoMoeda(null)).toBe("");
    expect(paraCampoMoeda(undefined)).toBe("");
    expect(paraCampoMoeda("")).toBe("");
  });
});

function campoFocado(valor: string, cursor: number): HTMLInputElement {
  const campo = document.createElement("input");
  document.body.append(campo);
  campo.value = valor;
  campo.focus();
  campo.setSelectionRange(cursor, cursor);
  return campo;
}

/** Simula digitação real, tecla a tecla: insere cada caractere na posição do cursor e dispara `input`, como o navegador faz. */
function digitar(campo: HTMLInputElement, texto: string): void {
  for (const char of texto) {
    const pos = campo.selectionStart ?? campo.value.length;
    campo.value = campo.value.slice(0, pos) + char + campo.value.slice(pos);
    campo.setSelectionRange(pos + 1, pos + 1);
    campo.dispatchEvent(new Event("input"));
  }
}

describe("ligarMascaraDeMoeda", () => {
  it("mascara enquanto digita", () => {
    const campo = campoFocado("", 0);
    ligarMascaraDeMoeda(campo);

    campo.value = "150000";
    campo.dispatchEvent(new Event("input"));
    expect(campo.value).toBe("1.500,00");
  });

  it("digitar tecla a tecla, do início ao fim, dá o mesmo resultado que atribuir o valor de uma vez", () => {
    const campo = campoFocado("", 0);
    ligarMascaraDeMoeda(campo);

    digitar(campo, "13220");
    expect(campo.value).toBe("132,20");
  });

  it("digitar tecla a tecla um valor menor que 3 dígitos (padding do centavo)", () => {
    const campo = campoFocado("", 0);
    ligarMascaraDeMoeda(campo);

    digitar(campo, "50");
    expect(campo.value).toBe("0,50");
  });

  it("cursor sempre termina no fim do campo após cada tecla", () => {
    const campo = campoFocado("", 0);
    ligarMascaraDeMoeda(campo);

    digitar(campo, "132");
    expect(campo.selectionStart).toBe(campo.value.length);
  });
});

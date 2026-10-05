import { describe, it, expect } from "vitest";
import { campo, regras, schema } from "./validators";

describe("Validadores", () => {
  describe("obrigatorio", () => {
    it("deve rejeitar string vazia", () => {
      const resultado = regras.obrigatorio("Campo")("");
      expect(resultado).not.toBeNull();
    });

    it("deve aceitar valor válido", () => {
      const resultado = regras.obrigatorio("Campo")("valor");
      expect(resultado).toBeNull();
    });
  });

  describe("email", () => {
    it("deve rejeitar email inválido", () => {
      const resultado = regras.email()("invalido");
      expect(resultado).not.toBeNull();
    });

    it("deve aceitar email válido", () => {
      const resultado = regras.email()("valid@example.com");
      expect(resultado).toBeNull();
    });

    it("deve rejeitar email sem domínio completo", () => {
      const resultado = regras.email()("test@test");
      expect(resultado).not.toBeNull();
    });
  });

  describe("minLength", () => {
    it("deve rejeitar texto curto", () => {
      const resultado = regras.minLength(3, "Campo")("ab");
      expect(resultado).not.toBeNull();
    });

    it("deve aceitar texto do tamanho correto", () => {
      const resultado = regras.minLength(3, "Campo")("abc");
      expect(resultado).toBeNull();
    });
  });

  describe("maxLength", () => {
    it("deve rejeitar texto longo", () => {
      const resultado = regras.maxLength(5, "Campo")("abcdef");
      expect(resultado).not.toBeNull();
    });

    it("deve aceitar texto dentro do limite", () => {
      const resultado = regras.maxLength(5, "Campo")("abcd");
      expect(resultado).toBeNull();
    });
  });

  describe("numero", () => {
    it("deve rejeitar não-número", () => {
      const resultado = regras.numero()("abc");
      expect(resultado).not.toBeNull();
    });

    it("deve aceitar número válido", () => {
      const resultado = regras.numero()("123");
      expect(resultado).toBeNull();
    });

    it("deve rejeitar NaN ou Infinity", () => {
      expect(regras.numero()("NaN")).not.toBeNull();
      expect(regras.numero()("Infinity")).not.toBeNull();
    });
  });

  describe("schema", () => {
    interface Formulario {
      nome: string;
      email: string;
    }

    const testSchema = schema<Formulario>({
      nome: campo("nome", [regras.obrigatorio("Nome")]),
      email: campo("email", [regras.email()]),
    });

    it("deve validar múltiplos campos", () => {
      const erros = testSchema({
        nome: "João",
        email: "joao@example.com",
      });
      expect(Object.keys(erros).length).toBe(0);
    });

    it("deve reportar múltiplos erros", () => {
      const erros = testSchema({
        nome: "",
        email: "invalido",
      });
      expect(Object.keys(erros).length).toBeGreaterThan(0);
      expect(erros.nome).toBeDefined();
      expect(erros.email).toBeDefined();
    });
  });
});

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ErroApi } from "@/api/http";
import { concluirConvitePendente, convitePendente } from "./convite-pendente";

beforeEach(() => sessionStorage.clear());
afterEach(() => vi.restoreAllMocks());

describe("convitePendente", () => {
  it("guarda, lê e limpa o token", () => {
    expect(convitePendente.obter()).toBeNull();
    convitePendente.definir("abc");
    expect(convitePendente.obter()).toBe("abc");
    convitePendente.limpar();
    expect(convitePendente.obter()).toBeNull();
  });

  it("não quebra quando o armazenamento está indisponível", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("bloqueado");
    });
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("bloqueado");
    });
    expect(() => convitePendente.definir("abc")).not.toThrow();
    expect(convitePendente.obter()).toBeNull();
  });
});

describe("concluirConvitePendente", () => {
  it("não faz nada sem convite pendente", async () => {
    const aceitar = vi.fn();
    const avisar = vi.fn();
    await concluirConvitePendente({ aceitar, avisar });
    expect(aceitar).not.toHaveBeenCalled();
    expect(avisar).not.toHaveBeenCalled();
  });

  it("aceita o convite pendente, avisa e limpa", async () => {
    convitePendente.definir("tok-1");
    const aceitar = vi.fn().mockResolvedValue({});
    const avisar = vi.fn();
    await concluirConvitePendente({ aceitar, avisar });
    expect(aceitar).toHaveBeenCalledWith("tok-1");
    expect(avisar).toHaveBeenCalledWith(expect.stringContaining("Convite aceito"));
    expect(convitePendente.obter()).toBeNull();
  });

  it("recusa do servidor mostra o motivo e também consome a pendência", async () => {
    convitePendente.definir("tok-2");
    const aceitar = vi.fn().mockRejectedValue(new ErroApi(403, "sem_permissao", "Este convite é para outro e-mail."));
    const avisar = vi.fn();
    await concluirConvitePendente({ aceitar, avisar });
    expect(avisar).toHaveBeenCalledWith("Este convite é para outro e-mail.");
    expect(convitePendente.obter()).toBeNull();
  });

  it("falha inesperada usa mensagem genérica, sem lançar, e limpa", async () => {
    convitePendente.definir("tok-3");
    const aceitar = vi.fn().mockRejectedValue(new Error("boom"));
    const avisar = vi.fn();
    await expect(concluirConvitePendente({ aceitar, avisar })).resolves.toBeUndefined();
    expect(avisar).toHaveBeenCalledWith(expect.stringContaining("Não foi possível aceitar"));
    expect(convitePendente.obter()).toBeNull();
  });
});

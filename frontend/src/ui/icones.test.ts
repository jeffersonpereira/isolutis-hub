import { beforeEach, describe, expect, it } from "vitest";
import { botaoIcone, icone, montarSprite, nomesDeIcones } from "./icones";

beforeEach(() => {
  document.body.innerHTML = "";
});

describe("icone", () => {
  it("ícone decorativo é oculto de leitores de tela", () => {
    const s = String(icone("clientes"));
    expect(s).toContain('aria-hidden="true"');
    expect(s).toContain('href="#i-clientes"');
    expect(s).not.toContain("aria-label");
  });

  it("com rótulo vira imagem com nome acessível", () => {
    const s = String(icone("alerta", { rotulo: "Atrasado" }));
    expect(s).toContain('role="img"');
    expect(s).toContain('aria-label="Atrasado"');
    expect(s).not.toContain("aria-hidden");
  });

  it("escapa o rótulo e a classe", () => {
    const s = String(icone("alerta", { rotulo: '"><script>x</script>', classe: 'a" onload="x' }));
    expect(s).not.toContain("<script>");
    expect(s).not.toContain('onload="x"');
  });

  it("nome inexistente devolve vazio, sem lançar", () => {
    expect(String(icone("nao-existe"))).toBe("");
  });
});

describe("botaoIcone", () => {
  it("usa o rótulo como nome acessível e dica", () => {
    const s = String(botaoIcone("fechar", "Fechar menu"));
    expect(s).toContain('aria-label="Fechar menu"');
    expect(s).toContain('title="Fechar menu"');
    expect(s).toContain('type="button"');
  });

  it("recusa botão só com ícone e sem nome", () => {
    expect(() => botaoIcone("fechar", "  ")).toThrow();
  });
});

describe("montarSprite", () => {
  it("injeta um único sprite com todos os ícones, mesmo se chamado de novo", () => {
    montarSprite();
    montarSprite();
    expect(document.querySelectorAll("#sprite-icones")).toHaveLength(1);
    const nomes = nomesDeIcones();
    expect(nomes.length).toBeGreaterThanOrEqual(30);
    for (const nome of nomes) expect(document.getElementById(`i-${nome}`)).not.toBeNull();
  });

  it("o sprite é oculto de tecnologias assistivas", () => {
    montarSprite();
    expect(document.getElementById("sprite-icones")?.getAttribute("aria-hidden")).toBe("true");
  });
});

describe("licença", () => {
  it("o cabeçalho do módulo cita Lucide e a licença ISC", async () => {
    const { readFileSync } = await import("node:fs");
    const { join } = await import("node:path");
    const fonte = readFileSync(join(process.cwd(), "src/ui/icones.ts"), "utf-8");
    expect(fonte).toContain("Lucide");
    expect(fonte).toContain("ISC");
  });
});

import { beforeEach, describe, expect, it } from "vitest";
import {
  aplicarLogo,
  aplicarPaleta,
  comContraste,
  contraste,
  cssDaPaleta,
  esquecerIdentidades,
  identidadeLembrada,
  lembrarIdentidade,
  misturar,
  PALETA_PADRAO,
  PALETAS_SUGERIDAS,
  textoSobre,
  tokensDaPaleta,
} from "./identidade";

const PNG = "data:image/png;base64,iVBORw0KGgo=";

beforeEach(() => {
  localStorage.clear();
  document.head.innerHTML = "";
  document.body.innerHTML = `<span id="logoSide"><img src="/aime-horizontal-reverso.svg" alt="AIME Tech"><img class="marca-min" src="/aime-simbolo-reverso.svg" alt="AIME Tech"></span>`;
});

describe("cores", () => {
  it("mistura e contraste seguem a WCAG", () => {
    expect(misturar("#000000", "#ffffff", 0.5)).toBe("#808080");
    expect(contraste("#000000", "#ffffff")).toBeCloseTo(21, 0);
    expect(textoSobre("#1a2d47")).toBe("#ffffff");
    expect(textoSobre("#f5d76e")).not.toBe("#ffffff");
  });

  it("escurece cores claras até o contraste mínimo e mantém as que já bastam", () => {
    expect(comContraste("#1a2d47", "#ffffff", 4.5)).toBe("#1a2d47");
    const ajustada = comContraste("#ffe066", "#ffffff", 4.5);
    expect(contraste(ajustada, "#ffffff")).toBeGreaterThanOrEqual(4.5);
  });

  it("toda paleta sugerida gera texto e menu legíveis", () => {
    for (const { paleta } of PALETAS_SUGERIDAS) {
      const { claro, escuro } = tokensDaPaleta(paleta);
      expect(contraste(claro["--teal-texto"]!, "#ffffff")).toBeGreaterThanOrEqual(4.5);
      expect(contraste(claro["--accent"]!, claro["--accent-ink"]!)).toBeGreaterThanOrEqual(4.5);
      expect(contraste(claro["--side-bg"]!, "#c6d0de")).toBeGreaterThanOrEqual(7);
      expect(contraste(escuro["--teal-texto"]!, "#151e2f")).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("uma primária clara demais vira um tom escuro legível", () => {
    const { claro } = tokensDaPaleta({ primaria: "#fff3b0", destaque: "#ffd60a" });
    expect(contraste(claro["--navy"]!, "#ffffff")).toBeGreaterThanOrEqual(4.5);
    expect(contraste(claro["--teal-texto"]!, "#ffffff")).toBeGreaterThanOrEqual(4.5);
  });
});

describe("aplicarPaleta", () => {
  it("injeta os tokens dos dois temas e remove ao voltar à padrão", () => {
    aplicarPaleta({ primaria: "#1b4332", destaque: "#40916c" });
    const estilo = document.getElementById("paleta-empresa");
    expect(estilo?.textContent).toContain("--teal:#40916c");
    expect(estilo?.textContent).toContain(':root[data-theme="dark"]{');
    aplicarPaleta(PALETA_PADRAO);
    expect(document.getElementById("paleta-empresa")).toBeNull();
    aplicarPaleta({ primaria: "#1b4332", destaque: "#40916c" });
    aplicarPaleta(null);
    expect(document.getElementById("paleta-empresa")).toBeNull();
  });

  it("o CSS gerado só atribui cores hexadecimais", () => {
    const css = cssDaPaleta({ primaria: "#123456", destaque: "#abcdef" });
    const valores = [...css.matchAll(/--[a-z-]+:([^;}]+)/g)].map((m) => m[1]);
    expect(valores.length).toBeGreaterThan(10);
    valores.forEach((v) => expect(v).toMatch(/^#[0-9a-f]{6}$/));
  });
});

describe("aplicarLogo", () => {
  it("troca as duas imagens do menu e volta à logo padrão", () => {
    aplicarLogo(PNG, "Alfa");
    const [grande, pequena] = Array.from(document.querySelectorAll("img"));
    expect(grande?.getAttribute("src")).toBe(PNG);
    expect(grande?.alt).toBe("Alfa");
    expect(pequena?.getAttribute("src")).toBe(PNG);
    expect(document.getElementById("logoSide")?.classList.contains("logo-propria")).toBe(true);
    aplicarLogo(null);
    expect(grande?.getAttribute("src")).toBe("/aime-horizontal-reverso.svg");
    expect(pequena?.getAttribute("src")).toBe("/aime-simbolo-reverso.svg");
    expect(document.getElementById("logoSide")?.classList.contains("logo-propria")).toBe(false);
  });
});

describe("memória local", () => {
  it("lembra por empresa, descarta valores inválidos e esquece ao sair", () => {
    lembrarIdentidade("e1", { logo: PNG, paleta: { primaria: "#111111", destaque: "#222222" } });
    expect(identidadeLembrada("e1")).toEqual({ logo: PNG, paleta: { primaria: "#111111", destaque: "#222222" } });
    expect(identidadeLembrada("e2")).toBeNull();
    localStorage.setItem("hub.identidade.e3", JSON.stringify({ logo: "javascript:alert(1)", paleta: { primaria: "red", destaque: "#000000" } }));
    expect(identidadeLembrada("e3")).toEqual({ logo: null, paleta: null });
    localStorage.setItem("hub.identidade.e4", "{não é json");
    expect(identidadeLembrada("e4")).toBeNull();
    esquecerIdentidades();
    expect(identidadeLembrada("e1")).toBeNull();
  });
});

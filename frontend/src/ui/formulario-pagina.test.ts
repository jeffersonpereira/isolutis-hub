import { beforeEach, describe, expect, it } from "vitest";
import { html } from "@/core/html";
import { podeSair, registrarVista, vistaAtual } from "@/state/nucleo";
import { abrirFormularioPagina, instantaneo, mostrarRegistroNaoEncontrado } from "./formulario-pagina";

function form(corpo: string): HTMLFormElement {
  const f = document.createElement("form");
  f.innerHTML = corpo;
  return f;
}

describe("instantaneo", () => {
  it("normaliza os valores e ignora botões, arquivos e campos desabilitados", () => {
    const f = form(`<input name="a" value="  x  "><input name="b" value="y" disabled><button name="c" value="1"></button><input name="d" type="file">`);
    expect(JSON.parse(instantaneo(f))).toEqual([["a", "x"]]);
  });

  it("caixas só contam quando marcadas", () => {
    const f = form(`<input type="checkbox" name="papel" value="cliente" checked><input type="checkbox" name="papel" value="fornecedor">`);
    expect(JSON.parse(instantaneo(f))).toEqual([["papel", "cliente"]]);
  });

  it("alterar e restaurar o valor dá o mesmo instantâneo", () => {
    const f = form(`<input name="nome" value="Alfa"><select name="uf"><option value="BA" selected>BA</option><option value="SP">SP</option></select>`);
    const antes = instantaneo(f);
    (f.elements.namedItem("nome") as HTMLInputElement).value = "Beta";
    expect(instantaneo(f)).not.toBe(antes);
    (f.elements.namedItem("nome") as HTMLInputElement).value = "Alfa";
    expect(instantaneo(f)).toBe(antes);
  });
});

const tick = (): Promise<void> => new Promise((r) => setTimeout(r, 10));
const campo = (): HTMLInputElement => document.querySelector<HTMLInputElement>("[name=nome]")!;
const digitar = (valor: string): void => {
  campo().value = valor;
  campo().dispatchEvent(new Event("input", { bubbles: true }));
};

async function abrir(): Promise<void> {
  await abrirFormularioPagina({
    vista: "clientes",
    rotuloLista: "Clientes",
    caminho: "/clientes/abc",
    titulo: "Distribuidora Alfa",
    avatar: "DA",
    secoes: [
      { id: "gerais", titulo: "Dados gerais", corpo: html`<input name="nome" value="Alfa">` },
      { id: "obs", titulo: "Observações", corpo: html`<textarea name="obs"></textarea>` },
    ],
    salvar: html`<button type="button" class="btn primary" data-salvar>Salvar</button>`,
    excluir: html`<button type="button" class="btn danger" data-excluir>Excluir</button>`,
    registro: { recurso: "clientes", id: "abc", versao: 3 },
  });
}

beforeEach(() => {
  document.body.innerHTML = '<div id="app"><nav id="nav"></nav><main id="view"></main></div>';
  history.replaceState(null, "", "/clientes");
});

describe("formulário em página", () => {
  registrarVista({ id: "clientes", nome: "Clientes", desenhar: () => html`<p>Lista</p>` });

  it("mostra a trilha, o título e as seções com navegação", async () => {
    await abrir();
    expect(document.querySelector(".trilha")?.textContent).toContain("Clientes");
    expect(document.querySelector(".fp-head h1")?.textContent).toBe("Distribuidora Alfa");
    expect([...document.querySelectorAll(".fp-sec h2")].map((e) => e.textContent)).toEqual(["Dados gerais", "Observações"]);
    expect(document.querySelectorAll(".fp-snav a")).toHaveLength(2);
    expect(location.pathname).toBe("/clientes/abc");
    await podeSair();
    await import("@/state/nucleo").then((n) => n.sairDaPagina());
  });

  it("sem alterações, sair não pede confirmação", async () => {
    await abrir();
    expect(document.querySelector(".fp-acoes")?.classList.contains("dirty")).toBe(false);
    expect(await podeSair()).toBe(true);
    expect(document.querySelector(".confirmar")).toBeNull();
    await import("@/state/nucleo").then((n) => n.sairDaPagina());
  });

  it("com alterações mostra o aviso e pede confirmação; continuar editando mantém tudo", async () => {
    await abrir();
    digitar("Beta");
    expect(document.querySelector(".fp-acoes")?.classList.contains("dirty")).toBe(true);
    const pergunta = podeSair();
    await tick();
    expect(document.querySelector(".confirmar")).not.toBeNull();
    document.querySelector<HTMLButtonElement>("[data-confirmar-nao]")!.click();
    expect(await pergunta).toBe(false);
    expect(document.querySelector(".confirmar")).toBeNull();
    expect(campo().value).toBe("Beta");
    await import("@/state/nucleo").then((n) => n.sairDaPagina());
  });

  it("descartar e sair permite a saída", async () => {
    await abrir();
    digitar("Beta");
    const pergunta = podeSair();
    await tick();
    document.querySelector<HTMLButtonElement>("[data-confirmar-sim]")!.click();
    expect(await pergunta).toBe(true);
    await import("@/state/nucleo").then((n) => n.sairDaPagina());
  });

  it("alterar e restaurar o valor não conta como alteração", async () => {
    await abrir();
    digitar("Beta");
    digitar("Alfa");
    expect(document.querySelector(".fp-acoes")?.classList.contains("dirty")).toBe(false);
    expect(await podeSair()).toBe(true);
    await import("@/state/nucleo").then((n) => n.sairDaPagina());
  });

  it("recarregar ou fechar a aba com alterações pede confirmação ao navegador; sem alterações, não", async () => {
    await abrir();
    const evento = (): BeforeUnloadEvent => {
      const e = new Event("beforeunload", { cancelable: true }) as BeforeUnloadEvent;
      window.dispatchEvent(e);
      return e;
    };
    expect(evento().defaultPrevented).toBe(false);
    digitar("Beta");
    expect(evento().defaultPrevented).toBe(true);
    await import("@/state/nucleo").then((n) => n.sairDaPagina());
    expect(evento().defaultPrevented).toBe(false); // ouvinte removido ao sair
  });

  it("sair do formulário destrava a área principal", async () => {
    await abrir();
    const { sairDaPagina, ir } = await import("@/state/nucleo");
    sairDaPagina();
    await ir("clientes", { historico: "nenhum", semGuarda: true });
    expect(document.querySelector("[data-formulario-pagina]")).toBeNull();
    expect(document.getElementById("view")?.textContent).toContain("Lista");
    expect(vistaAtual()).toBe("clientes");
  });
});

describe("registro não encontrado", () => {
  it("explica o que houve e oferece o caminho de volta", async () => {
    document.body.innerHTML = '<div id="app"><nav id="nav"></nav><main id="view"></main></div>';
    mostrarRegistroNaoEncontrado({ vista: "clientes", rotuloLista: "Clientes" });
    expect(document.querySelector("h1")?.textContent).toBe("Registro não encontrado");
    const voltar = document.querySelector<HTMLAnchorElement>(".empty a");
    expect(voltar?.getAttribute("href")).toBe("/clientes");
    expect(voltar?.dataset.go).toBe("clientes");
    await import("@/state/nucleo").then((n) => n.sairDaPagina());
  });
});

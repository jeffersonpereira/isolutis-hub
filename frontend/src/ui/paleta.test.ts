import { describe, expect, it, vi } from "vitest";
import { filtrarItens, montarItens, normalizar, type ItemDaPaleta } from "./paleta";

const item = (rotulo: string, grupo: ItemDaPaleta["grupo"] = "Ir para"): ItemDaPaleta => ({ grupo, rotulo, icone: "painel", executar: () => {} });
const rotulos = (itens: ItemDaPaleta[]): string[] => itens.map((i) => i.rotulo);

describe("normalizar", () => {
  it("ignora acentos, cedilha e caixa", () => {
    expect(normalizar("Orçamentos")).toBe("orcamentos");
    expect(normalizar("  AÇÃO  ")).toBe("acao");
    expect(normalizar("Relatórios")).toBe("relatorios");
  });
});

describe("filtrarItens", () => {
  const todos = [item("Painel"), item("Clientes"), item("Orçamentos"), item("Novo orçamento", "Ações"), item("Plano de Contas"), item("Despesas e investimentos")];

  it("consulta vazia devolve tudo, na ordem original", () => {
    expect(filtrarItens(todos, "")).toEqual(todos);
    expect(filtrarItens(todos, "   ")).toEqual(todos);
  });

  it("encontra sem acento e sem diferenciar caixa", () => {
    expect(rotulos(filtrarItens(todos, "orcamen"))).toEqual(["Orçamentos", "Novo orçamento"]);
    expect(rotulos(filtrarItens(todos, "ORÇAM"))).toContain("Orçamentos");
  });

  it("começo do texto vem antes de começo de palavra, que vem antes de 'contém'", () => {
    const itens = [item("Fluxo de Caixa"), item("Conta Bancária"), item("Plano de Contas"), item("Contatos")];
    expect(rotulos(filtrarItens(itens, "conta"))).toEqual(["Conta Bancária", "Contatos", "Plano de Contas"]);
  });

  it("sem correspondência devolve lista vazia", () => {
    expect(filtrarItens(todos, "xyz")).toEqual([]);
  });

  it("não busca registros: um nome de cliente não aparece", () => {
    expect(filtrarItens(todos, "distribuidora alfa")).toEqual([]);
  });
});

describe("montarItens", () => {
  const fontes = () => ({
    telas: [{ id: "clientes", nome: "Clientes" }, { id: "conta", nome: "Minha conta" }],
    acoes: [{ id: "novoCliente", rotulo: "Novo cliente", icone: "clientes" }, { id: "novaTarefa", rotulo: "Nova tarefa" }],
    iconeDaTela: (id: string) => `i-${id}`,
    irPara: vi.fn(),
    executarAcao: vi.fn(),
  });

  it("lista as telas e depois as ações, com o grupo certo", () => {
    const itens = montarItens(fontes());
    expect(itens.map((i) => `${i.grupo}:${i.rotulo}`)).toEqual(["Ir para:Clientes", "Ir para:Minha conta", "Ações:Novo cliente", "Ações:Nova tarefa"]);
  });

  it("usa o ícone da tela e o da ação (ou um padrão)", () => {
    const itens = montarItens(fontes());
    expect(itens.map((i) => i.icone)).toEqual(["i-clientes", "i-conta", "clientes", "mais"]);
  });

  it("executar chama a navegação ou a ação certa", () => {
    const f = fontes();
    const itens = montarItens(f);
    itens[0]?.executar();
    itens[2]?.executar();
    expect(f.irPara).toHaveBeenCalledWith("clientes");
    expect(f.executarAcao).toHaveBeenCalledWith("novoCliente");
  });

  it("sem ações (modo leitura) só há telas", () => {
    const itens = montarItens({ ...fontes(), acoes: [] });
    expect(itens.every((i) => i.grupo === "Ir para")).toBe(true);
  });
});

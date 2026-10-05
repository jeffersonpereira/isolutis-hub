// E2E do módulo financeiro: menu em grupo, plano de contas em árvore, conta bancária, parceiro, título e fluxo de caixa.
import { chromium } from "playwright";

const BASE = process.env.HUB_URL ?? "http://localhost:8000";
const EMAIL = process.env.HUB_EMAIL ?? "admin@isolutis.com.br";
const SENHA = process.env.HUB_SENHA ?? "senha-segura-123";
const sufixo = String(Date.now()).slice(-6);
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
const page = await (await browser.newContext({ viewport: { width: 1360, height: 900 } })).newPage();
const erros = [];
page.on("console", (m) => { if (m.type() === "error" && !/ERR_CERT|401|fonts|422|Já existe|CNPJ inválido|Há títulos/.test(m.text())) erros.push("console: " + m.text()); });
page.on("pageerror", (e) => erros.push("pageerror: " + e.message));
const passo = (n) => console.log("✔", n);
// CNPJ válido e único por execução (calcula os dígitos verificadores)
const digito = (base, pesos) => { const r = base.split("").reduce((s, d, i) => s + Number(d) * pesos[i], 0) % 11; return r < 2 ? 0 : 11 - r; };
const baseCnpj = ("1" + sufixo + "0001").slice(0, 12).padEnd(12, "0");
const d1 = digito(baseCnpj, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
const d2 = digito(baseCnpj + d1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
const cnpj = baseCnpj + d1 + d2;
const cnpjFmt = cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, "$1.$2.$3/$4-$5");
const cnpjErrado = cnpj.slice(0, 13) + ((Number(cnpj[13]) + 1) % 10);
// toLocaleString("pt-BR") usa espaço não separável (U+00A0) entre R$ e o valor
const visao = async () => ((await page.textContent("#view")) ?? "").replace(/\u00a0/g, " ");
const toast = async () => (await page.locator(".toast").last().textContent().catch(() => "")) ?? "";

await page.goto(`${BASE}/`);
await page.fill("#lgEmail", EMAIL);
await page.fill("#lgSenha", SENHA);
await page.click("#lgBotao");
await page.waitForSelector("nav button");

// menu Financeiro com os submenus do spec
const sub = async () => page.$$eval("nav .nav-sub button", (b) => b.map((x) => x.textContent.replace(/\d+$/, "").trim()));
await page.click('nav .nav-grupo');
await page.waitForTimeout(200);
const subs = await sub();
console.log("submenus:", subs.join(" | "));
for (const s of ["Plano de Contas", "Conta Bancária", "Parceiro de Negócio", "Títulos Financeiros"]) if (!subs.includes(s)) throw new Error("falta submenu " + s);
passo("menu Financeiro com submenus");

// plano de contas
await page.click('nav button[data-go="fin-plano"]');
await page.waitForTimeout(500);
// clicar numa conta alterna a seleção: só clica se ainda não estiver selecionada
const selecionar = async (nome) => {
  const linha = page.locator(`.tree-row:has-text("${nome}")`).first();
  if ((await linha.getAttribute("aria-selected")) !== "true") await linha.click();
};
const criarConta = async (pai, codigoEsperado, nome, tipo, natureza) => {
  if (pai) await selecionar(pai);
  await page.click('[data-act="novaConta"]');
  await page.waitForSelector(".drawer");
  await page.waitForFunction((c) => document.querySelector("#f-codigo").value === c, codigoEsperado, { timeout: 4000 });
  await page.fill("#f-nome", nome);
  if (!(await page.isDisabled("#f-tipo_conta"))) await page.selectOption("#f-tipo_conta", tipo);
  if (natureza && !(await page.isDisabled("#f-natureza"))) await page.selectOption("#f-natureza", natureza);
  await page.click("[data-salvar]");
  await page.waitForSelector(".drawer", { state: "detached" });
};
const raiz = String(100 + Number(sufixo.slice(-3)) % 800); // código de raiz único por execução
await page.click('[data-act="novaConta"]').catch(() => {});
await page.waitForSelector(".drawer");
await page.fill("#f-codigo", raiz); await page.fill("#f-nome", `Receita ${sufixo}`);
await page.selectOption("#f-tipo_conta", "S"); await page.selectOption("#f-natureza", "R");
await page.click("[data-salvar]");
await page.waitForSelector(".drawer", { state: "detached" });
await criarConta(`Receita ${sufixo}`, `${raiz}.01`, `Contrato ${sufixo}`, "S");
await criarConta(`Contrato ${sufixo}`, `${raiz}.01.001`, `GT ${sufixo}`, "A");
if (!(await page.textContent(".tree")).includes(`${raiz}.01.001`)) throw new Error("árvore sem o 3º nível");
passo("plano de contas em árvore (3 níveis, código sugerido, natureza herdada)");

// conta analítica não aceita filhas: botão "nova conta" desabilitado ao selecionar a analítica
await selecionar(`GT ${sufixo}`);
if (!(await page.isDisabled('[data-act="novaConta"]'))) throw new Error("permitiu filha de analítica");
passo("conta analítica não aceita filhas na interface");

// despesas: mais um ramo para testar RN04
await page.click(`.tree-row:has-text("GT ${sufixo}")`); // desmarca (clicar de novo alterna)
const rDesp = String(Number(raiz) + 1);
await page.click('[data-act="novaConta"]'); await page.waitForSelector(".drawer");
await page.fill("#f-codigo", rDesp); await page.fill("#f-nome", `Despesa ${sufixo}`);
await page.selectOption("#f-tipo_conta", "S"); await page.selectOption("#f-natureza", "D");
await page.click("[data-salvar]"); await page.waitForSelector(".drawer", { state: "detached" });
await criarConta(`Despesa ${sufixo}`, `${rDesp}.01`, `Pessoal ${sufixo}`, "S");
await criarConta(`Pessoal ${sufixo}`, `${rDesp}.01.001`, `Salário ${sufixo}`, "A");

// conta bancária
await page.click('nav button[data-go="fin-contas"]'); await page.waitForTimeout(400);
await page.click('[data-act="novaContaBancaria"]'); await page.waitForSelector(".drawer");
await page.selectOption("#f-instituicao_financeira_id", { label: "001 · Banco do Brasil S.A." });
await page.fill("#f-nome", `Conta ${sufixo}`); await page.fill("#f-saldo_inicial", "1.000,00");
await page.click("[data-salvar]"); await page.waitForSelector(".drawer", { state: "detached" });
// duplicada: recusa
await page.click('[data-act="novaContaBancaria"]'); await page.waitForSelector(".drawer");
await page.selectOption("#f-instituicao_financeira_id", { label: "001 · Banco do Brasil S.A." });
await page.fill("#f-nome", `conta ${sufixo}`);
await page.click("[data-salvar]"); await page.waitForTimeout(600);
if (!/já existe/i.test(await toast())) throw new Error("não recusou conta duplicada: " + (await toast()));
await page.keyboard.press("Escape");
passo("conta bancária criada; duplicada recusada");

// parceiro (CNPJ inválido, depois válido)
await page.click('nav button[data-go="fin-parceiros"]'); await page.waitForTimeout(400);
await page.click('[data-act="novoParceiro"]'); await page.waitForSelector(".drawer");
await page.check('input[name="papel"][value="fornecedor"]'); await page.fill("#f-cpf_cnpj", cnpjErrado); await page.fill("#f-nome", `Fornecedor ${sufixo}`);
await page.selectOption("#f-uf", "BA");
await page.waitForFunction(() => document.querySelectorAll("#f-municipio_id option").length > 100, null, { timeout: 5000 });
await page.selectOption("#f-municipio_id", { label: "Salvador" });
await page.click("[data-salvar]"); await page.waitForTimeout(700);
if (!/CNPJ inválido/.test(await toast())) throw new Error("não validou CNPJ: " + (await toast()));
await page.fill("#f-cpf_cnpj", cnpjFmt);
await page.click("[data-salvar]"); await page.waitForSelector(".drawer", { state: "detached" });
if (!(await page.textContent("#view")).includes(cnpjFmt)) throw new Error("parceiro sem documento formatado");
passo("parceiro: CNPJ validado, município por UF");

// título: a receber só oferece contas de receita; a pagar, de despesa
await page.click('nav button[data-go="fin-titulos"]'); await page.waitForTimeout(400);
await page.click('[data-act="novoTitulo"]'); await page.waitForSelector(".drawer");
const opcoes = async () => page.$$eval("#f-plano_conta_id option", (o) => o.map((x) => x.textContent));
const rec = await opcoes();
if (!rec.some((t) => t.includes(`GT ${sufixo}`)) || rec.some((t) => t.includes(`Salário ${sufixo}`))) throw new Error("RN04 (receber) falhou: " + rec.slice(0, 5));
if (rec.some((t) => t.includes(`Contrato ${sufixo}`))) throw new Error("listou conta sintética");
await page.selectOption("#f-tipo_conta", "P");
const pag = await opcoes();
if (!pag.some((t) => t.includes(`Salário ${sufixo}`)) || pag.some((t) => t.includes(`GT ${sufixo}`))) throw new Error("RN04 (pagar) falhou");
passo("RN03/RN04 na interface: só analíticas, filtradas por tipo");
await page.selectOption("#f-tipo_conta", "R");
await page.selectOption("#f-plano_conta_id", { label: `${raiz}.01.001 GT ${sufixo}` });
await page.selectOption("#f-conta_bancaria_id", { label: `Conta ${sufixo} (001)` });
await page.selectOption("#f-parceiro_id", { label: `Fornecedor ${sufixo} · ${cnpjFmt}` });
const hoje = new Date().toISOString().slice(0, 10);
await page.fill("#f-data_vencimento", hoje);
await page.fill("#f-valor_titulo", "1.500,00"); await page.fill("#f-valor_multa", "10,50");
if (!(await page.textContent("#devido")).includes("1.510,50")) throw new Error("valor devido: " + (await page.textContent("#devido")));
await page.click("[data-salvar]"); await page.waitForSelector(".drawer", { state: "detached" });
await page.waitForTimeout(400);
if (!(await visao()).includes("R$ 1.510,50")) throw new Error("título não listado");
// quitar
await page.click(`tbody tr:has-text("GT ${sufixo}") >> text=Editar`); await page.waitForSelector(".drawer");
await page.selectOption("#f-status", "Q");
if (!(await page.isVisible("#f-data_pagamento"))) throw new Error("campos de quitação não apareceram");
await page.fill("#f-data_pagamento", hoje);
await page.click("[data-salvar]"); await page.waitForSelector(".drawer", { state: "detached" });
await page.waitForTimeout(400);
if (!(await page.textContent("#view")).includes("Quitado")) throw new Error("não quitou");
passo("título lançado, valor devido calculado e quitado");

// fluxo de caixa
await page.click('nav button[data-go="fin-fluxo"]'); await page.waitForTimeout(700);
const fluxo = await visao();
if (!fluxo.includes("Fluxo de caixa mensal") || !fluxo.includes("Saldo inicial de")) throw new Error("fluxo não carregou");
// a linha do mês atual (marcada "atual") mostra a entrada realizada do título quitado
const realizada = ((await page.locator("tbody tr:has-text('atual') td").nth(1).textContent()) ?? "").replace(/\u00a0/g, " ");
if (!/R\$ [\d.]+,\d{2}/.test(realizada)) throw new Error("mês atual sem entrada realizada: " + realizada);
await page.screenshot({ path: "financeiro-fluxo.png", fullPage: true });
passo("fluxo de caixa mensal exibe o recebimento");

// excluir (confirmação em gaveta) e bloqueio por vínculo
await page.click('nav button[data-go="fin-contas"]'); await page.waitForTimeout(400);
await page.click(`tbody tr:has-text("Conta ${sufixo}") >> text=Excluir`); await page.waitForSelector(".drawer");
await page.click("[data-confirmar]"); await page.waitForTimeout(700);
if (!/títulos/i.test(await toast())) throw new Error("deveria bloquear a exclusão: " + (await toast()));
passo("exclusão de conta com título é bloqueada com mensagem clara");
console.log("ERROS:", JSON.stringify(erros));
if (erros.length) process.exitCode = 1;
await browser.close();

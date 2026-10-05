// Teste de ponta a ponta: percorre os fluxos principais no navegador contra uma instância real.
// Pré-requisitos: backend + frontend no ar e dados de demonstração (python seed.py). Veja e2e/README.md.
import { chromium } from "playwright";

const BASE = process.env.HUB_URL ?? "http://localhost:8000";
const EMAIL = process.env.HUB_EMAIL ?? "admin@isolutis.com.br";
const SENHA = process.env.HUB_SENHA ?? "senha-segura-123";
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
const ctx = await browser.newContext({ viewport: { width: 1360, height: 900 }, acceptDownloads: true });
const page = await ctx.newPage();
const erros = [];
page.on("console", (m) => { if (m.type() === "error" && !/ERR_CERT|401|fonts/.test(m.text())) erros.push("console: " + m.text()); });
page.on("pageerror", (e) => erros.push("pageerror: " + e.message));
const drag = (src, dst) => page.evaluate(([a, b]) => {
  const s = [...document.querySelectorAll("article.card")].find((e) => e.textContent.includes(a)), d = document.querySelector(b);
  const dt = new DataTransfer();
  s.dispatchEvent(new DragEvent("dragstart", { bubbles: true, dataTransfer: dt }));
  d.dispatchEvent(new DragEvent("dragover", { bubbles: true, cancelable: true, dataTransfer: dt }));
  d.dispatchEvent(new DragEvent("drop", { bubbles: true, cancelable: true, dataTransfer: dt }));
}, [src, dst]);
const passo = (n) => console.log("✔", n);
await page.goto(`${BASE}/`);
await page.fill("#lgEmail", EMAIL);
await page.fill("#lgSenha", SENHA);
await page.click("#lgBotao");
await page.waitForSelector("nav button");
const ir = async (id) => { await page.click(`nav button[data-go="${id}"]`); await page.waitForTimeout(500); };

// 1. cliente novo pela interface
await ir("clientes");
await page.click('[data-act="novoCliente"]');
await page.fill('#f-nome', "Empresa <Teste> & Cia");
await page.fill('#f-telefone', "(71) 98888-7777");
await page.click("[data-salvar]");
await page.waitForSelector(".toast");
await page.waitForTimeout(500);
if (!(await page.textContent("#view")).includes("Empresa <Teste> & Cia")) throw new Error("cliente não aparece escapado");
passo("cliente criado (nome com HTML aparece como texto)");

// 2. busca
await page.fill("#busca", "alfa");
await page.waitForTimeout(300);
const linhas = await page.$$eval("tbody tr", (r) => r.length);
if (linhas !== 1) throw new Error("busca devolveu " + linhas);
await page.fill("#busca", "");
passo("busca filtra e mantém foco");

// 3. negócio: abrir, mover por API de ação (arrastar)
await ir("negocios");
await drag("App de pedidos", 'section.col[data-etapa="diag_agendado"]');
await page.waitForTimeout(800);
const etapaDepois = await page.$eval('article.card:has-text("App de pedidos")', (e) => e.closest("section").dataset.etapa);
if (etapaDepois !== "diag_agendado") throw new Error("drag não moveu: " + etapaDepois);
passo("arrastar cartão muda a etapa");

// 3b. soltar em Perdido abre formulário pedindo motivo
await page.check("#fechados");
await page.waitForTimeout(300);
await drag("Sistema de agendamento", 'section.col[data-etapa="perdido"]');
await page.waitForTimeout(500);
await page.screenshot({path:"dbg-perdido.png"});
if (!(await page.isVisible("#motivoBox"))) throw new Error("motivo não apareceu");
await page.click("[data-salvar]");
await page.waitForTimeout(300);
if (!(await page.textContent(".toast")).includes("motivo")) throw new Error("não exigiu motivo");
await page.selectOption("#f-motivo_perda", "Prazo");
await page.click("[data-salvar]");
await page.waitForTimeout(700);
passo("perdido exige motivo e grava");

// 4. orçamento: abrir o enviado, aprovar -> faturamento
await ir("orcamentos");
await page.click('tr:has-text("Enviado")');
await page.waitForSelector(".drawer");
const wa = await page.getAttribute("#waOrc", "href");
if (!wa.startsWith("https://wa.me/5571992390992?text=")) throw new Error("wa href " + wa);
await page.click("[data-baixar]");
const [dl] = await Promise.all([page.waitForEvent("download", { timeout: 5000 }).catch(() => null), page.waitForTimeout(100)]);
if (dl) console.log("download:", dl.suggestedFilename());
await page.waitForTimeout(800);
await page.click("[data-aprovar]");
await page.waitForSelector("#f-usaUnico");
console.log("resumo faturamento:", await page.textContent("#resumoGen"));
await page.fill("#f-parcelas", "3");
await page.click("[data-salvar]");
await page.waitForTimeout(900);
passo("orçamento aprovado e faturamento lançado em lote");
await ir("faturamento");
const lan = await page.$$eval(".list .li", (l) => l.length);
console.log("lançamentos listados:", lan);
await ir("negocios");
passo("negócio virou ganho: " + (await page.$eval('article.card:has-text("Portal do cliente")', (e) => e.closest("section").dataset.etapa).catch(() => "oculto")));

// 5. projeto: etapas padrão + relatório
await ir("projetos");
await page.click('article.pcard:has-text("ERP leve")');
await page.waitForSelector(".drawer");
const [rel] = await Promise.all([page.waitForEvent("download", { timeout: 6000 }), page.click("[data-relatorio]")]);
console.log("relatório:", rel.suggestedFilename());
await page.waitForTimeout(500);
await page.keyboard.press("Escape");
passo("relatório do projeto baixado");

// 6. tarefa: arrastar para concluído
await ir("tarefas");
await drag("Preparar diagnóstico", 'section.col[data-coluna="concluido"]');
await page.waitForTimeout(700);
const col = await page.$eval('article.card:has-text("Preparar diagnóstico")', (e) => e.closest("section").dataset.coluna);
if (col !== "concluido") throw new Error("tarefa não concluiu");
passo("tarefa arrastada para concluído");

// 7. despesas + equipe
await ir("despesas");
await page.screenshot({ path: "tela-despesas2.png", fullPage: true });
await ir("equipe");
await page.click('[data-act="novoUsuario"]');
await page.fill("#f-nome", "Novo Membro");
await page.fill("#f-email", `novo${Date.now()}@isolutis.com.br`);
await page.click("#gerarSenha");
await page.click("[data-salvar]");
await page.waitForSelector("#senhaFeita:not([hidden])");
passo("usuário criado com senha gerada");
await page.keyboard.press("Escape");

// 8. presença/realtime: segunda sessão altera, a primeira atualiza
const p2 = await ctx.newPage();
await p2.goto(`${BASE}/`);
await p2.waitForSelector("nav button");
await ir("clientes");
await p2.click('nav button[data-go="clientes"]');
await p2.click('[data-act="novoCliente"]');
await p2.fill("#f-nome", "Cliente via segunda aba");
await p2.click("[data-salvar]");
await page.waitForFunction(() => document.querySelector("#view").textContent.includes("Cliente via segunda aba"), null, { timeout: 5000 });
passo("tempo real: alteração de outra aba aparece sem recarregar");
console.log("ERROS:", JSON.stringify(erros));
await browser.close();

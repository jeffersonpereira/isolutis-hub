/** Testes para sistema de validação. */

import { campo, regras, schema } from "./validators";

// Teste simples de regras
console.log("🧪 Testando validators...");

// Teste: obrigatorio
let resultado = regras.obrigatorio("Campo")("");
console.assert(resultado !== null, "❌ obrigatorio não detectou string vazia");
resultado = regras.obrigatorio("Campo")("valor");
console.assert(resultado === null, "❌ obrigatorio rejeitou valor válido");
console.log("✅ obrigatorio");

// Teste: email
resultado = regras.email()("invalido");
console.assert(resultado !== null, "❌ email não detectou email inválido");
resultado = regras.email()("valid@example.com");
console.assert(resultado === null, "❌ email rejeitou email válido");
console.log("✅ email");

// Teste: minLength
resultado = regras.minLength(3, "Campo")("ab");
console.assert(resultado !== null, "❌ minLength não detectou texto curto");
resultado = regras.minLength(3, "Campo")("abc");
console.assert(resultado === null, "❌ minLength rejeitou texto válido");
console.log("✅ minLength");

// Teste: maxLength
resultado = regras.maxLength(5, "Campo")("abcdef");
console.assert(resultado !== null, "❌ maxLength não detectou texto longo");
resultado = regras.maxLength(5, "Campo")("abcd");
console.assert(resultado === null, "❌ maxLength rejeitou texto válido");
console.log("✅ maxLength");

// Teste: numero
resultado = regras.numero()("abc");
console.assert(resultado !== null, "❌ numero não detectou não-número");
resultado = regras.numero()("123");
console.assert(resultado === null, "❌ numero rejeitou número válido");
console.log("✅ numero");

// Teste: schema com múltiplos campos
interface Formulario {
  nome: string;
  email: string;
}

const testSchema = schema<Formulario>({
  nome: campo("nome", [
    regras.obrigatorio("Nome"),
    regras.minLength(3, "Nome"),
  ]),
  email: campo("email", [
    regras.obrigatorio("Email"),
    regras.email(),
  ]),
});

// Caso sucesso
let r = testSchema.parse({ nome: "João Silva", email: "joao@example.com" });
console.assert(r.sucesso === true, "❌ schema rejeitou dados válidos");
if (r.sucesso) {
  console.assert(r.dados.nome === "João Silva", "❌ schema perdeu dados");
  console.log("✅ schema: dados válidos");
}

// Caso falha: nome faltando
r = testSchema.parse({ nome: "", email: "joao@example.com" });
console.assert(r.sucesso === false, "❌ schema aceitou nome vazio");
if (!r.sucesso) {
  console.assert("nome" in r.erros, "❌ schema não reportou erro em nome");
  console.log("✅ schema: detecciona nome vazio");
}

// Caso falha: email inválido
r = testSchema.parse({ nome: "João", email: "invalido" });
console.assert(r.sucesso === false, "❌ schema aceitou email inválido");
if (!r.sucesso) {
  console.assert("email" in r.erros, "❌ schema não reportou erro em email");
  console.log("✅ schema: detecciona email inválido");
}

console.log("✅ Todos os testes passaram!");

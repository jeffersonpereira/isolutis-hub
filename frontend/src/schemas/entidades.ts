/** Schemas de validação para entidades principais. */

import { campo, regras, schema } from "@/ui/validators";

/** Validação para criação de novo usuário. */
export const usuarioCriarSchema = schema<{
  nome: string;
  email: string;
  senha: string;
}>({
  nome: campo("nome", [
    (valor: unknown) => regras.obrigatorio("Nome")(valor as string),
    (valor: unknown) => regras.minLength(3, "Nome")(valor as string),
    (valor: unknown) => regras.maxLength(150, "Nome")(valor as string),
  ]),
  email: campo("email", [
    (valor: unknown) => regras.obrigatorio("E-mail")(valor as string),
    (valor: unknown) => regras.email()(valor as string),
  ]),
  senha: campo("senha", [
    (valor: unknown) => regras.obrigatorio("Senha")(valor as string),
    (valor: unknown) => regras.minLength(8, "Senha")(valor as string),
  ]),
});

/** Validação para atualizar usuário existente. */
export const usuarioAtualizarSchema = schema<{
  nome: string;
  senha?: string;
}>({
  nome: campo("nome", [
    (valor: unknown) => regras.obrigatorio("Nome")(valor as string),
    (valor: unknown) => regras.minLength(3, "Nome")(valor as string),
    (valor: unknown) => regras.maxLength(150, "Nome")(valor as string),
  ]),
  senha: campo("senha", [
    // Senha pode estar vazia ao atualizar
  ]),
});

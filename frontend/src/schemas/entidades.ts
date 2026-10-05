/** Schemas de validação para entidades principais. */

import { campo, regras, schema } from "@/ui/validators";
import type { Usuario } from "@/api/tipos";

/** Validação para criação de novo usuário. */
export const usuarioCriarSchema = schema<{
  nome: string;
  email: string;
  senha: string;
}>({
  nome: campo("nome", [
    regras.obrigatorio("Nome"),
    regras.minLength(3, "Nome"),
    regras.maxLength(150, "Nome"),
  ]),
  email: campo("email", [
    regras.obrigatorio("E-mail"),
    regras.email(),
  ]),
  senha: campo("senha", [
    regras.obrigatorio("Senha"),
    regras.minLength(8, "Senha"),
  ]),
});

/** Validação para atualizar usuário existente. */
export const usuarioAtualizarSchema = schema<{
  nome: string;
  senha?: string;
}>({
  nome: campo("nome", [
    regras.obrigatorio("Nome"),
    regras.minLength(3, "Nome"),
    regras.maxLength(150, "Nome"),
  ]),
  senha: campo("senha", [
    // Senha pode estar vazia ao atualizar
  ]),
});

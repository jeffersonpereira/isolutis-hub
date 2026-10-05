# Guia de Testes - isolutis-hub

## Testes Unitários

Validadores estão em `frontend/src/ui/validators.test.ts`. 

Teste manualmente:
```bash
cd frontend
node --loader tsx src/ui/validators.test.ts
```

## Testes E2E - Fluxo Crítico: Criar Usuário

### Pré-requisitos
- [ ] Banco Supabase está rodando
- [ ] Backend está rodando
- [ ] Frontend está rodando (`npm run dev` ou acesso a http://localhost:5173)
- [ ] Você está logado como ADMIN

### Passos de Teste

#### 1. Navegar para Usuários
- [ ] Abrir aba "Administração" no menu lateral
- [ ] Clicar em "Usuários do sistema"
- [ ] Verificar que lista de usuários carrega

#### 2. Criar Novo Usuário (Sucesso)
- [ ] Clicar em "Novo usuário"
- [ ] Formulário abre em gaveta
- [ ] Preencher:
  - Nome: "João Teste Silva"
  - E-mail: "joao.teste@empresa.com"
  - Senha: clicar "Gerar senha" (deve preencher com 12 caracteres aleatórios)
  - Admin: deixar desmarcado
- [ ] Clicar "Criar usuário"
- [ ] **Esperado:**
  - ✅ Toast "Usuário criado"
  - ✅ Banner verde com informações de acesso aparece
  - ✅ Botão "Copiar" funciona
  - ✅ Banner desaparece automaticamente após 5 segundos
  - ✅ Gaveta fecha
  - ✅ Nova linha aparece na tabela

#### 3. Validação de Campos Obrigatórios
- [ ] Clicar "Novo usuário" novamente
- [ ] Clicar "Criar usuário" SEM preencher campos
- [ ] **Esperado:**
  - ✅ Toast "Informe o nome"
  - ✅ Gaveta permanece aberta
  - ✅ Formulário não foi enviado

#### 4. Validação de E-mail
- [ ] Preencher nome: "Teste"
- [ ] Preencher e-mail: "invalido" (sem @)
- [ ] Preencher senha: "senha123"
- [ ] Clicar "Criar usuário"
- [ ] **Esperado:** Toast indica e-mail inválido (se backend validar)

#### 5. Validação de Senha (Mínimo 8 caracteres)
- [ ] Preencher nome: "Teste"
- [ ] Preencher e-mail: "valido@test.com"
- [ ] Preencher senha: "abc123" (menos de 8)
- [ ] Clicar "Criar usuário"
- [ ] **Esperado:**
  - ✅ Toast "A senha precisa ter pelo menos 8 caracteres"

#### 6. Editar Usuário Existente
- [ ] Na lista, clicar na linha do usuário criado
- [ ] Gaveta abre com dados preenchidos
- [ ] Alterar nome para "João Teste Silva Junior"
- [ ] Deixar senha vazia (não trocar)
- [ ] Clicar "Salvar"
- [ ] **Esperado:**
  - ✅ Toast "Salvo"
  - ✅ Gaveta fecha
  - ✅ Tabela atualiza com novo nome

#### 7. Trocar Senha de Usuário
- [ ] Clicar novamente no usuário
- [ ] Preencher "Nova senha": "novaSenha123"
- [ ] Clicar "Salvar"
- [ ] **Esperado:**
  - ✅ Banner verde com informações de acesso
  - ✅ Desaparece após 5 segundos

#### 8. Remover Usuário (Desativar)
- [ ] Clicar novamente no usuário
- [ ] Clicar "Remover da equipe"
- [ ] Confirmar em dialog (se houver)
- [ ] **Esperado:**
  - ✅ Toast "Usuário removido da equipe"
  - ✅ Linha na tabela mostra "Removido" no campo "Acesso"

### Casos de Erro

#### Erro de Conexão
- [ ] Desligar internet (ou mock com DevTools)
- [ ] Tentar criar usuário
- [ ] **Esperado:** Toast genérico de conexão

#### Erro de Autorização (Não é Admin)
- [ ] Fazer logout
- [ ] Logar com usuário NÃO-admin
- [ ] Tentar acessar "Usuários do sistema"
- [ ] **Esperado:** Página vazia ou mensagem de acesso negado

#### Email Duplicado
- [ ] Tentar criar usuário com mesmo e-mail
- [ ] **Esperado:** Erro do backend (verificar toast)

## Testes de Regressão

### Após Qualquer Mudança em `equipe.ts`
- [ ] Executar fluxo "Criar Novo Usuário (Sucesso)" completo
- [ ] Verificar que banner de senha desaparece após 5s
- [ ] Verificar que validações funcionam

### Após Mudança em `estado.ts` ou `nucleo.ts`
- [ ] Abrir múltiplas abas
- [ ] Fazer mudança em uma aba
- [ ] Verificar que outra aba recarrega em tempo real

## Automação Futura (Playwright/Cypress)

Template para teste automatizado (pseudo-código):

```typescript
// e2e/usuario-criar.spec.ts
test("Criar novo usuário com sucesso", async ({ page }) => {
  await page.goto("http://localhost:5173");
  
  // Login
  await page.fill('[data-test="email"]', "admin@empresa.com");
  await page.fill('[data-test="senha"]', "senha");
  await page.click('[data-test="login"]');
  await page.waitForNavigation();
  
  // Navegar para usuários
  await page.click('[href="#equipe"]');
  await page.waitForLoadState("networkidle");
  
  // Criar novo
  await page.click('[data-act="novoUsuario"]');
  
  // Preencher
  await page.fill('[name="nome"]', "Teste Silva");
  await page.fill('[name="email"]', "teste@empresa.com");
  await page.click('#gerarSenha');
  
  // Salvar
  await page.click('[data-salvar]');
  
  // Verificar sucesso
  await expect(page.locator(".tst-sucesso")).toBeVisible();
  
  // Verificar que senha desaparece após 5s
  await page.waitForTimeout(6000);
  await expect(page.locator('[id="senhaFeita"]')).toHaveAttribute('hidden');
});
```

## Checklist Pré-Release

- [ ] Todos os testes E2E passam
- [ ] Não há console.error em DevTools (exceto logs esperados)
- [ ] Performance: criação de usuário em < 2 segundos
- [ ] Responsive: funciona em mobile
- [ ] Acessibilidade: teclado navegável
- [ ] Segurança: nenhuma senha exposta em cookies/localStorage (apenas token)

## Problemas Conhecidos

(Nenhum registrado por enquanto - adicionar conforme encontrado)

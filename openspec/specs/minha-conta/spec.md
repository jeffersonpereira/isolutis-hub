# minha-conta Specification

## Purpose
Tela pessoal acessível a qualquer usuário autenticado, com as preferências de segurança da própria conta: autenticação em dois fatores e troca de senha.

## Requirements
### Requirement: Tela "Minha conta" para todo usuário autenticado
O sistema SHALL oferecer a tela "Minha conta" a qualquer usuário autenticado, independentemente do papel na empresa ativa.

#### Scenario: Membro comum acessa Minha conta
- **WHEN** um usuário sem papel de administrador abre o menu de navegação
- **THEN** o item "Minha conta" está disponível
- **AND** a tela abre sem exigir permissão de administrador

#### Scenario: Dados da empresa continuam exclusivos de administradores
- **WHEN** um usuário sem papel de administrador abre o menu de navegação
- **THEN** o item "Dados da empresa" não é exibido
- **AND** a tela "Minha conta" não contém campos de edição da empresa

---

### Requirement: Preferência pessoal de autenticação em dois fatores
O sistema SHALL permitir, na tela "Minha conta", que o usuário veja o estado do próprio 2FA e escolha ativá-lo ou desativá-lo. A escolha SHALL valer apenas para a conta do usuário que a fez.

#### Scenario: Estado do 2FA exibido ao abrir a tela
- **WHEN** o usuário abre "Minha conta"
- **THEN** a seção de segurança exibe se o 2FA está ativado ou desativado para a sua conta
- **AND** oferece a ação correspondente ("Ativar 2FA" ou "Desativar 2FA")

#### Scenario: Ativar 2FA a partir de Minha conta
- **WHEN** o usuário clica em "Ativar 2FA"
- **THEN** o fluxo de configuração de `autenticacao-2fa` é conduzido na própria tela
- **AND** ao concluir, o estado passa a "Ativado"

#### Scenario: Desativar 2FA a partir de Minha conta
- **WHEN** o usuário clica em "Desativar 2FA" e confirma com um código válido
- **THEN** o estado passa a "Desativado"

#### Scenario: Escolha de um usuário não afeta outros
- **WHEN** um usuário ativa ou desativa o próprio 2FA
- **THEN** nenhum outro usuário da mesma empresa tem o seu 2FA alterado

---

### Requirement: Troca de senha acessível em Minha conta
O sistema SHALL oferecer, na tela "Minha conta", o acesso à troca da própria senha.

#### Scenario: Usuário abre a troca de senha
- **WHEN** o usuário clica em "Trocar senha" na tela "Minha conta"
- **THEN** o formulário de troca de senha existente é aberto

# Proposal

## Why

O Hub é um SaaS multiempresa, mas hoje só existe um caminho para colocar um novo cliente no ar: um script de terminal
(`criar_admin.py`) que a AIME Tech roda com credencial de banco. Não há tela para criar uma empresa, nem para ver quais
empresas existem, quem são os usuários de cada uma ou corrigir um acesso (papel errado, pessoa que saiu, convite
perdido). A tela "Equipe" só enxerga a empresa ativa e só para o `admin` dela. O operador da plataforma precisa dessa
visão e dessas ações dentro do produto, sem ganhar acesso aos dados de negócio dos clientes.

## What Changes

- Nova identidade **operador da plataforma**, separada dos papéis de empresa. Só operadores acessam a nova área.
- Nova **área da plataforma** (`/plataforma`) com: lista de empresas (nome, CNPJ, usuários ativos, status), **criar
  empresa** informando o e-mail do administrador inicial (que recebe um convite por e-mail), **suspender e reativar**
  empresa, e **gerir membros** de qualquer empresa (ver, convidar, trocar papel, desativar, reenviar convite).
- Empresa passa a ter **status** (ativa ou suspensa). Empresa suspensa não aparece na escolha de empresa e recusa
  requisições, com os dados preservados.
- **Auditoria** de toda ação do operador (quem, quando, empresa, ação, antes e depois).
- Rotas `/plataforma/*` usam um **papel de banco próprio**, sem acesso às tabelas de negócio. O papel da aplicação
  continua sem poder criar empresas.
- O script `criar_admin.py` ganha `--operador` para criar o primeiro operador.
- O operador **não** vê financeiro, clientes, orçamentos nem outros dados de negócio de nenhuma empresa.

## Capabilities

### New Capabilities
- `area-plataforma`: identidade do operador, acesso restrito, listagem, criação e suspensão de empresas, gestão de
  membros por empresa, regra do último administrador e auditoria das ações.

### Modified Capabilities
- `provisionamento-de-empresas`: a criação continua exclusiva do operador, que agora também a faz pela área da
  plataforma (além do script), com convite ao administrador inicial em vez de senha pelo terminal.
- `selecao-empresa`: empresas suspensas ficam fora da lista de escolha e são recusadas como empresa ativa.

## Impact

- **Banco**: migração 0017 (com script de volta): tabela `operador_plataforma`, coluna `status` em `empresa`, tabela
  `auditoria_plataforma`, papel `hub_plataforma` e funções `SECURITY DEFINER` de provisionamento e gestão de membros.
- **Backend**: nova credencial/pool (`HUB_PLATAFORMA_DATABASE_URL`), `deps.operador_atual`, `routers/plataforma.py`,
  `services/plataforma.py`; `deps.empresa_atual` e `GET /empresas` passam a considerar o status da empresa; convites
  emitidos pelo operador para empresa sem administrador ainda.
- **Frontend**: nova vista `features/plataforma.ts` e item de menu visível só ao operador; `GET /me` informa se o
  usuário é operador.
- **Operação**: nova variável de ambiente e role de banco a provisionar em cada ambiente; o primeiro operador é criado
  pelo script.
- **Dados existentes**: todas as empresas atuais ficam `ativa`.

## Context

`empresa` tem `id`, `nome`, `segmento`, `onboarding_concluido` e carimbos; a tela só edita o nome via `api.empresas.atualizar(nome)`. Parceiros já têm `tipo_pessoa` (PJ/PF) + `cpf_cnpj`, endereço e município (`municipio` com UF), validação de CPF/CNPJ em `financeiro/regras.py`. A CSP restringe `connect-src` a `'self'`. Existe `app/ratelimit.py`.

## Goals / Non-Goals

**Goals:**
- Cadastro completo da empresa, aditivo e retrocompatível.
- Consulta de CNPJ segura, reutilizável por qualquer tela.
- Inscrição (tipo + número) sempre como primeiros campos.

**Non-Goals:**
- Criação de empresas por usuários (continua operação de plataforma — `multi-empresa-sessao`).
- Upload de logo, certificado digital, emissão fiscal.
- Consulta de CPF em serviços externos.

## Decisions

- **Colunas na própria `empresa`** (1:1), todas anuláveis na migração: `tipo_inscricao` (`CNPJ|CPF`), `inscricao` (somente dígitos), `razao_social`, `nome_fantasia`, `inscricao_estadual`, `inscricao_municipal`, `cnae_codigo`, `cnae_descricao`, `regime_tributario`, `situacao_cadastral`, `data_abertura`, `email`, `telefone`, `cep`, `logradouro`, `numero`, `complemento`, `bairro`, `municipio_id`. `nome` continua sendo o nome de exibição. Alternativa: tabela separada de endereço — descartada (um endereço por empresa, sem histórico).
- **Unicidade**: índice único parcial em `(tipo_inscricao, inscricao)` onde `inscricao IS NOT NULL`. CNPJ/CPF validado por dígito verificador no backend (reuso de `regras.py`).
- **Proxy `GET /cnpj/{cnpj}`**: exige usuário autenticado, normaliza para 14 dígitos, valida DV antes de sair, chama URL fixa da BrasilAPI (sem URL vinda do cliente → sem SSRF), timeout curto, cache em memória por poucas horas, rate limit por usuário, mapeia 404→"CNPJ não encontrado", 429/5xx/timeout→"serviço indisponível, preencha manualmente". Resposta é um DTO próprio (não repassa o payload bruto). Não loga o CNPJ além do necessário.
- **Preenchimento no front**: ao completar 14 dígitos válidos (blur ou ao digitar o último), chama o proxy, mostra estado "Buscando…" e preenche somente campos retornados; não apaga o que o usuário já digitou sem avisar (preenche campos vazios; para os preenchidos, sobrescreve só na ação explícita ou em campos derivados da consulta). Falha nunca bloqueia o cadastro manual.
- **Município**: casar `municipio` por código IBGE/nome+UF; se não achar, deixar para escolha manual.
- **Ordem**: `tipo de inscrição` → `número` → demais campos como hoje. Em parceiros, `tipo_pessoa` (PJ/PF) é o tipo de inscrição e `cpf_cnpj` o número.

## Risks / Trade-offs

- [BrasilAPI indisponível/limitada] → cache, rate limit, mensagem clara, cadastro manual sempre possível.
- [Dados públicos desatualizados sobrescrevendo dados do usuário] → preencher só vazios por padrão; usuário revisa antes de salvar.
- [Empresas existentes sem inscrição] → colunas anuláveis; tela orienta completar, sem bloquear uso.
- [Reordenar telas em uso] → mudança visual apenas; sem mudança de contrato.

## Migration Plan

1. Migração aditiva + down (remover colunas e índice). 2. Backend/DTOs/router CNPJ. 3. Front. 4. Rollback: reverter app e rodar down; dados novos descartados.

## Open Questions

- Campos fiscais (regime tributário, CNAE) são apenas informativos nesta change; uso fiscal fica para outra.

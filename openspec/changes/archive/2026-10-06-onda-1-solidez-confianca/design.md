## Context

O iSolutis Hub é um ERP/CRM multi-tenant (FastAPI + TypeScript vanilla + PostgreSQL via Neon/Supabase). Esta onda agrupa seis iniciativas independentes que precisam ser entregues antes da comercialização. A maioria não tem dependência entre si e pode ser desenvolvida em paralelo; as exceções são documentadas em **Decisions**.

Estado atual crítico:
- Deploy é 100% manual, sem CI/CD
- `services/painel.py` carrega todos os negócios e orçamentos em memória para calcular o funil
- Orçamento gera HTML; clientes esperam PDF
- Novo membro recebe senha criada pelo admin por canal externo (WhatsApp, oral)
- Tokens CSS têm nomes que contradizem os valores (`--gold` é azul-verde) e 9 tamanhos de fonte sem tokens

## Goals / Non-Goals

**Goals:**
- Automatizar o ciclo de build/test/deploy completamente
- Eliminar os carregamentos em memória do painel (queries agregadas no banco)
- Entregar PDF real nos orçamentos
- Substituir criação manual de senha por convite por e-mail com token
- Unificar o sistema de design (tokens, fontes locais, nomes de módulos)
- Adicionar sinalização visual de vencimentos no faturamento
- Adicionar zona de alertas ativos no painel

**Non-Goals:**
- Redesign visual da aplicação (cores, layout, hierarquia)
- Notificações por e-mail além do convite de equipe
- Envio automático do orçamento por e-mail (só geração do PDF)
- Alterações nos endpoints existentes além dos mencionados explicitamente

## Decisions

### D1 — Geração de PDF: WeasyPrint vs Playwright

**Escolhido: WeasyPrint**

| Critério          | WeasyPrint            | Playwright (Chromium) |
|-------------------|-----------------------|-----------------------|
| Tamanho da imagem | +~15MB                | +~400MB               |
| Fidelidade CSS    | Boa para layout A4    | Excelente             |
| Dependência       | Python puro           | Binário externo       |
| Manutenção        | Simples               | Complexa              |

Playwright já está no projeto, mas apenas em `devDependencies` do frontend para E2E. Adicioná-lo ao runtime do backend Docker inflaria a imagem em ~400MB desnecessariamente. WeasyPrint cobre o caso de uso (PDF de orçamento A4 com tabela de itens).

**Alternativa se WeasyPrint não passar nos testes de layout:** usar `pdfkit` com `wkhtmltopdf` já embutido no Dockerfile.

---

### D2 — Token de convite: JWT vs UUID aleatório em banco

**Escolhido: UUID aleatório armazenado em banco**

JWT seria stateless, mas um convite precisa ser invalidado quando aceito ou expirado. Com JWT não há como revogar sem blacklist. UUID em banco é simples, auditável e já segue o padrão das demais entidades do projeto.

Tabela: `convites (id uuid PK, token uuid UNIQUE, email citext, empresa_id uuid FK, papel text, criado_por uuid FK, expira_em timestamptz, usado_em timestamptz)`.

Token expira em 72h. Após uso, `usado_em` é preenchido e o token é recusado.

---

### D3 — Fontes: self-hosted vs system fonts

**Escolhido: self-hosted `.woff2`**

System fonts (ex: `system-ui`) eliminariam a dependência, mas a identidade visual do produto usa Montserrat e IBM Plex Sans de forma deliberada. Trocar por fontes de sistema mudaria a aparência do produto. Self-hosted resolve o problema de privacidade (sem requisição ao Google Fonts) sem mudar a identidade.

Fontes geradas com `fontsquirrel.com` ou `google-webfonts-helper`, apenas os pesos usados (Montserrat 600, IBM Plex Sans 400/500, IBM Plex Mono 400).

---

### D4 — Queries do painel: agregação no banco vs cache

**Escolhido: queries agregadas no banco**

Cache (Redis ou in-memory) adicionaria complexidade e estado distribuído. O banco Neon com índices compostos por `empresa_id` já suporta `GROUP BY + SUM` eficientemente. As queries do painel são lidas isoladas por tenant — exatamente o que o RLS + índices cobrem bem.

Índices relevantes (já existentes após migração 0005):
- `ix_negocios_empresa_etapa_previsao ON negocios (empresa_id, etapa, previsao, id)`
- `ix_orcamentos_empresa_enviados ON orcamentos (empresa_id, data, id) WHERE status = 'enviado'`

---

### D5 — Zona de alertas: polling vs evento

**Escolhido: calculado no endpoint `/painel` existente**

O painel já é recarregado a cada mudança de recurso via WebSocket (mecanismo de realtime existente). Não é necessário polling separado. Os alertas são calculados nas mesmas queries do painel e retornados como novos campos no schema `Painel`.

---

### D6 — Renomeação de tokens CSS: migração gradual vs big bang

**Escolhido: big bang com find-replace**

Os tokens `--gold`, `--gold-soft` são usados em ~12 arquivos CSS e ~0 arquivos TS (não são expostos ao JS). A renomeação é mecânica e 100% rastreável via `grep`. Uma migração gradual com aliases temporários (`--gold: var(--teal-mid)`) cria confusão durante a transição. Big bang com commit atômico é mais seguro aqui.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| WeasyPrint tem comportamento diferente de browser para CSS complexo | Testar template de orçamento com dados reais antes de fazer deploy; manter fallback HTML |
| Convite por e-mail depende de SMTP configurado; se não configurado em produção, o flow quebra silenciosamente | Validar `HUB_SMTP_*` em `validar_para_producao()` junto com `secret_key` |
| Big bang nos tokens CSS pode introduzir regressão visual em tela não testada | Smoke test visual nas 12 telas após o commit |
| CI/CD primeiro deploy pode falhar se secrets do GitHub não estiverem configurados | Documentar todos os secrets necessários no `README` antes de habilitar o pipeline |
| Skeleton de loading usa `--bg-hover` que não existe no tokens atual | Corrigir para `--sunk` (token existente) antes de aplicar |

## Migration Plan

**Ordem recomendada de entrega (cada item é um PR independente):**

1. CI/CD pipeline — sem risco, não toca código de aplicação
2. Tokens CSS + fontes + nomes de módulos — frontend only, deploy atômico
3. Faturamento: sinalização visual — frontend only, sem backend
4. Painel: queries + skeleton + alertas — backend + frontend, testar com dados reais
5. Orçamentos: PDF — backend, requer `weasyprint` no Dockerfile
6. Convite de equipe — backend (migração) + frontend, testar fluxo completo

**Rollback:** cada item é reversível individualmente. A migração de `convites` tem `down` trivial (DROP TABLE). Tokens CSS: reverter o commit. PDF: reverter para `text/html` no endpoint.

## Open Questions

- **SMTP para convites**: qual provedor usar em produção? (SendGrid, Resend, SMTP próprio?) Precisa de decisão antes de implementar o convite.
- **Alertas de painel**: qual o threshold de "orçamento sem resposta há X dias"? Proposta inicial: 15 dias. Confirmar com produto.
- **PDF com logo**: o template de orçamento deve incluir o logo da empresa? Se sim, `Empresa` precisa de campo `logo_url`.

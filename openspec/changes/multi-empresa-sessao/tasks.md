## 1. Pré-requisitos e auditoria

- [x] 1.1 Reconferir a base: `correcoes-imediatas-convite-2fa-menu` e `design-system-e-shell` estão arquivadas; reler `main.ts`, `barra-superior.ts`, `roteador.ts` e `paleta.ts` antes de alterar. Anotar quais changes pendentes (`corrigir-titulo-plano-contas-e-2fa-minha-conta`, `combobox-pesquisavel`, `empresa-completa-e-consulta-cnpj`) já foram aplicadas, para listar as rotas novas na tarefa 3.3
- [x] 1.2 Confirmação obtida em 2026-10-07: relatórios (DRE e fluxo de caixa) em `financeiro` e lista mínima de clientes em `base`
- [x] 1.3 Auditar `schemas/painel.py` e `services/painel.py`, listando cada bloco do painel e a permissão que o protege (`comercial` ou `financeiro`)
- [x] 1.4 Verificar no banco se alguma view, trigger, função ou política depende de `usuarios.admin` antes do `DROP COLUMN`
- [x] 1.5 Procurar usos de `criar_empresa` e de `papel="membro"` em `backend/tests/`, `e2e/` e scripts, para saber o que precisa de atualização
- [x] 1.6 Verificar o uso de `dados.negocios`, `dados.clientes`, `dados.orcamentos` e `dados.produtos` nas telas de papel básico (`projetos`, `tarefas`, `painel`) e nas financeiras (`faturamento`, `despesas`)
- [x] 1.7 Levantar todos os usos de `eu.admin`, `usuario.admin`, `estado.usuario.admin` e `somenteAdmin` (`nucleo.ts`, `main.ts`, `ui/onboarding.ts`, `features/equipe.ts`, telas financeiras e `roteador.test.ts`)
- [x] 1.8 Mapear as três superfícies que listam telas e ações (menu em `renderMenu`, paleta em `itensAtuais`, `acoesRapidas`) e a resolução de rota em `state/roteador.ts`/`caminhos.ts`

## 2. Migração do banco (0010)

- [x] 2.1 Criar `migrations/sql/0010_papeis_multi_empresa.sql`: converter `usuario_empresa` e `convites` pendentes de `membro` para `comercial`; trocar `ck_usuario_empresa_papel` para `admin`, `financeiro`, `comercial`, `membro`; remover `usuarios.admin`; revogar `EXECUTE` de `criar_empresa(text)` de `hub_runtime`
- [x] 2.2 Criar `0010_papeis_multi_empresa_down.sql`: recriar `usuarios.admin` (default falso), converter `comercial` e `financeiro` em `membro` (documentar a perda de informação no arquivo), restaurar a constraint antiga e o `GRANT`
- [x] 2.3 Criar `migrations/versions/0010_papeis_multi_empresa.py` seguindo o padrão de `0008` e `0009` e ligar `down_revision = "0009"`
- [ ] 2.4 Atualizar `tests_sql/test_schema.sql` e `docs/MULTI_TENANCY.md` com a nova constraint, a remoção do flag e a restrição da função (parcial: `docs/MULTI_TENANCY.md` atualizado; `tests_sql/test_schema.sql` só cobre o schema 0001, não foi alterado)
- [ ] 2.5 Aplicar e reverter a migration num banco de teste com dados de papéis mistos, conferindo as contagens antes e depois

## 3. Backend: papéis e permissões

- [x] 3.1 Criar `app/domain/papeis.py` com o conjunto único de papéis válidos, o tipo de permissão e o mapa `PERMISSOES_POR_PAPEL`
- [x] 3.2 Em `app/deps.py`, criar `exige(permissao)` (fábrica de dependência sobre `empresa_atual` e a membership) e reimplementar `administrador` como `exige("administracao")`
- [x] 3.3 Aplicar as permissões em `main.py` e nos routers conforme a matriz: `comercial` em clientes, negócios, orçamentos e produtos; `financeiro` em `/financeiro/*`, hub de parceiros, faturamento, despesas e relatórios; `administracao` em usuários, convites, `PATCH /empresas/ativa` (inclusive o cadastro completo da empresa) e onboarding; `base` nas demais rotas de dados, em `/auth/*` (2FA de Minha conta) e em `GET /cnpj/{cnpj}`
- [x] 3.4 Fazer `GET /empresas` devolver `papel` e `permissoes` por empresa
- [x] 3.5 Criar `GET /clientes/referencias` (somente `id` e `nome`, permissão `base`) em `routers/clientes.py`, mantendo `GET /clientes` completo em `comercial`
- [x] 3.6 Em `routers/painel.py` e `services/painel.py`, preencher cada bloco só se o papel tiver a permissão mapeada na auditoria; os demais blocos saem `null`
- [x] 3.7 Remover `POST /empresas` e o schema `EmpresaNova` de `routers/equipe.py`
- [x] 3.8 Atualizar `scripts/criar_admin.py` para gravar `papel="admin"` sem usar `Usuario.admin`

## 4. Backend: usuários e convites com `papel`

- [x] 4.1 Em `models/usuario.py`, remover `Usuario.admin`
- [x] 4.2 Em `schemas/usuario.py`, substituir `admin: bool` por `papel` em `UsuarioLeitura` (opcional, nulo em `/auth/eu`), `UsuarioCriar` e `UsuarioAtualizar`, validando contra `app/domain/papeis.py`
- [x] 4.3 Em `schemas/convite.py`, trocar o padrão do papel de `^(admin|membro)$` para a lista de papéis válidos
- [x] 4.4 Em `services/usuarios.py`, trocar o uso de `admin` por `papel` na listagem, criação e atualização, preservando "não rebaixar nem desativar a si mesmo" e "pelo menos um administrador ativo"
- [x] 4.5 Em `services/convites.py`, aplicar o papel do convite na membership e usar o conjunto único de papéis
- [x] 4.6 Regenerar `backend/openapi.json` e `frontend/src/api/schema.d.ts` (`npm run gen:api`)

## 5. Testes do backend

- [x] 5.1 Criar fixtures de usuário por papel (`admin`, `financeiro`, `comercial`, `membro`) em `tests/conftest.py`
- [x] 5.2 Criar `tests/test_permissoes.py` parametrizado pela matriz: para cada papel, rotas representativas de cada permissão respondem 200 ou 403 conforme esperado
- [x] 5.3 Criar o teste que percorre `app.routes` sob `/api/v1` e falha para qualquer rota sem `exige(...)` fora da lista explícita de rotas públicas
- [x] 5.4 Testar `GET /empresas` (papel e permissões por empresa), `GET /clientes/referencias` (somente `id` e `nome`, acessível a `membro`) e o bloqueio de `GET /clientes` completo sem `comercial`
- [x] 5.5 Testar o painel por papel (blocos ausentes para `membro`, completos para `admin`)
- [x] 5.6 Testar isolamento entre empresas: mesmo usuário em duas empresas com papéis diferentes, listagens separadas, e recusa de empresa sem membership
- [x] 5.7 Testar atribuição de papel (só `admin`, papel inválido, não rebaixar a si mesmo, último administrador) e convite com cada um dos quatro papéis
- [x] 5.8 Testar que `POST /empresas` não existe e que a conexão da aplicação não executa `criar_empresa`
- [x] 5.8a Testar que `GET /cnpj/{cnpj}` responde 200 a todos os papéis autenticados (com o serviço externo simulado) e que a atualização completa da empresa responde 403 a quem não é `admin`
- [ ] 5.9 Atualizar os testes existentes que usam `papel="membro"` esperando acesso comercial (`test_multi_tenant.py`, `test_auth_equipe.py` e demais) e os que leem `admin` no schema (parcial: `conftest.py` ajustado para a empresa e o papel; os demais testes de integração já estavam desatualizados em relação ao multi-tenant antes desta change e precisam de revisão própria)

## 6. Frontend: sessão e escolha de empresa

- [x] 6.1 Em `api/http.ts`, fazer `sessaoToken.empresa()` ler `sessionStorage`; `definirEmpresa` grava em `sessionStorage` e em `localStorage` (última usada), ambos com `try/catch`; adicionar limpeza de ambos no logout
- [x] 6.2 Em `api/endpoints.ts`, tipar `GET /empresas` com `papel` e `permissoes` e criar o tipo `Permissao`
- [x] 6.3 Criar `ui/escolha-empresa.ts` com a tela "Em qual empresa quer trabalhar?": cartões com nome e papel, "última usada" pré-selecionada, estado de lista vazia com ação de sair, foco e navegação por teclado
- [x] 6.4 Em `main.ts`, substituir `selecionarEmpresa()` pela nova etapa, depois da autenticação e do convite pendente e antes de `resolverRotaInicial`: manter a empresa da aba se ainda constar em `/empresas`; senão exibir a escolha; guardar `permissoes` da empresa ativa no estado; resolver a URL de destino só após a escolha
- [x] 6.5 Em `ui/barra-superior.ts`, reescrever `blocoEmpresa()` para ler empresa e papel do estado (sem `#empresaAtiva` nem `#empresaDoMenu`), exibir "Empresa · Papel" e a ação "Trocar de empresa" (limpa a escolha da aba e recarrega) no cabeçalho do menu do usuário; remover o `<select id="empresaAtiva">` de `index.html`
- [x] 6.6 Tratar o 403 de `empresa_atual` em `api/http.ts`: limpar a escolha da aba e recarregar, reabrindo a tela
- [x] 6.7 Aplicar estilos da tela de escolha e do bloco de empresa do menu do usuário usando os tokens do design system, com tema claro/escuro, responsivo e acessível

## 7. Frontend: permissões

- [x] 7.1 Em `state/estado.ts`, remover `eu.admin` e guardar o papel e as permissões da empresa ativa, com um helper `temPermissao(p)`; migrar todos os usos levantados em 1.7 (incluindo `ui/onboarding.ts`, que hoje decide por `estado.usuario?.admin`)
- [x] 7.2 Em `state/nucleo.ts`, trocar `Vista.somenteAdmin` por `Vista.permissao?: Permissao` e criar `vistaPermitida(v)`; usar essa única função no menu (`renderMenu`), na paleta (`ui/paleta.ts`) e em `acoesRapidas`
- [x] 7.2a Em `state/roteador.ts`/`caminhos.ts`, fazer `resolverRotaInicial` usar `vistaPermitida`: URL de tela sem permissão cai no painel e corrige o endereço; atualizar `roteador.test.ts`
- [x] 7.3 Em `state/nucleo.ts`, declarar a permissão de cada carregador; fazer `carregarTudo()` e `recarregar()` executarem só os permitidos com `Promise.allSettled`, e ignorar avisos do WebSocket de recursos não permitidos
- [x] 7.4 Carregar `dados.referenciasClientes` (via `/clientes/referencias`) para todos e trocar `nomeCliente` e `seletorCliente` para usá-lo; manter `dados.clientes` completo só com `comercial`
- [x] 7.5 Migrar as vistas `empresa`, `equipe`, `fin-*`, `faturamento`, `despesas`, `relatorios` e as comerciais de `somenteAdmin`/sem restrição para a `permissao` correta, e registrar `ORDEM_MENU` conforme necessário
- [x] 7.6 Fazer `projetos.ts` degradar sem `comercial` (seletor "Negócio vendido" vazio, sem aviso de ganhos sem projeto)
- [x] 7.7 Em `features/painel.ts`, omitir os blocos ausentes na resposta
- [x] 7.8 Em `features/equipe.ts` e `ui/convite.ts`, trocar o checkbox de administrador por um select com os quatro papéis, e exibir o papel na listagem de equipe e de convites pendentes
- [x] 7.9 Remover `api.empresas.criar` e qualquer referência a criação de empresa pela interface, se existirem

## 8. Testes do frontend e e2e

- [x] 8.1 Testes unitários (vitest) de `temPermissao`, de `vistaPermitida` (menu, paleta e "+ Novo" coerentes), da rota inicial por permissão e da lógica de escolha de empresa (empresa da aba válida, ausente, não mais acessível, lista vazia, última usada)
- [x] 8.2 Teste do armazenamento por aba: `sessionStorage` por aba, `localStorage` como última usada, limpeza no logout
- [ ] 8.3 Atualizar `e2e/` (seed e `login-2fa.spec.ts`) para a etapa de escolha de empresa e criar casos: usuário com duas empresas escolhe e troca; `membro` abre sem erro; `comercial` não vê Financeiro; URL direta de tela sem permissão cai no painel; link para tela permitida abre após a escolha de empresa; convite pendente com duas empresas; troca de empresa não mostra dados da anterior

## 9. Validação final

- [ ] 9.1 Rodar a suíte backend (`pytest`) e confirmar que passa, incluindo o teste de rotas sem permissão
- [ ] 9.2 Rodar `npm run typecheck`, `npm run lint`, `npm test` e os e2e no frontend
- [ ] 9.3 Verificar manualmente, no navegador, cada papel (admin, financeiro, comercial, membro): menu, painel, carga sem erros no console e recusa por URL direta da API
- [ ] 9.4 Verificar manualmente duas abas com empresas diferentes e a troca de empresa pelo menu do usuário da barra superior
- [ ] 9.5 Atualizar a documentação (`docs/MULTI_TENANCY.md`, `docs/ARQUITETURA.md`) com papéis, matriz e provisionamento de empresas
- [ ] 9.6 Revisar o diff final quanto a segurança, regressões e complexidade desnecessária

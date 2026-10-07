## 1. Direção visual e linha de base (ponto de parada)

- [x] 1.1 Gerar mockups em HTML (`mockups/index.html`, navegável, com claro e escuro, desktop e celular, verificado no navegador sem erros de JavaScript) de três telas, nos temas claro e escuro: casca com listagem de clientes (barra superior, barra lateral com ícones, cabeçalho, barra de ferramentas e tabela), formulário de cliente em página (seções, navegação entre seções, barra de ações fixa) e a paleta de comandos com o menu do usuário e a alternância de tema
- [x] 1.2 Obter a aprovação do usuário sobre a direção visual dos mockups e registrar ajustes pedidos; **não começar o grupo 2 antes disso**. Aprovado sem ajustes, com o escopo do mockup (cartões de indicadores, filtros por chip e menu em seções entram; o campo "Papéis" e o aviso de CPF/CNPJ ficam para `parceiros-por-papel`)
- [x] 1.3 Criar o script de varredura de capturas (Playwright, API simulada) que abre todas as telas em claro, escuro e celular, e guardar as capturas "antes" fora do repositório. Script em `e2e/visual/` (fixtures geradas do OpenAPI do backend); linha de base: 54 capturas, com rolagem horizontal da página já existente só em Orçamentos no celular
- [x] 1.4 Confirmar com o ambiente de produção que um caminho aninhado devolve o `index.html` ao recarregar; se não devolver, corrigir a configuração de fallback antes do grupo 6. **Não devolvia**: o front estático (projeto Vercel `isolutis-hub-client`, raiz `frontend`) responde 404 a todo caminho que não seja `/`, inclusive `/convite/<token>` (link do e-mail de convite) e `/login/2fa`. Criado `frontend/vercel.json` com rewrite para `/index.html`; a confirmação em produção depende do deploy do front (tarefa 10.4)

## 2. Tokens e ícones

- [x] 2.1 Em `styles/tokens.css`, acrescentar os tokens de espaçamento (`--esp-1` a `--esp-8`), raios (`--r-sm`, `--r-md`, `--r-lg`, `--r-full`), camadas (`--z-topbar`, `--z-gaveta`, `--z-modal`, `--z-paleta`, `--z-toast`), alturas de controle (`--controle-sm`, `--controle-md`, `--controle-lg`), o fundo da área principal (`--canvas`) e medidas da casca (`--topbar-h`, `--sidebar-w` com 272px, `--sidebar-w-recolhida`)
- [x] 2.2 Substituir os `z-index` literais dos CSS (gaveta, scrim, toast e demais) pelos tokens de camada
- [x] 2.3 Criar `ui/icones.ts` com o cabeçalho de atribuição (Lucide, licença ISC), os traçados de ~30 ícones (menu, painel, clientes, negócios, orçamentos, projetos, tarefas, produtos, financeiro, faturamento, relatórios, equipe, empresa, conta, busca, mais, fechar, recolher, sol, lua, monitor, sair, chave, alerta, erro, vazio, seta e demais usados), a função que injeta o sprite uma vez, `icone(nome, { rotulo? })` e `botaoIcone(nome, rotulo)`
- [x] 2.4 Garantir que nome de ícone inexistente não gera erro visível
- [x] 2.5 Estilos base de `.ico` (tamanho, alinhamento com o texto, cor herdada)
- [x] 2.6 Testes unitários (vitest) de `icone` e `botaoIcone`: decorativo oculto, com rótulo vira imagem, botão exige nome, nome inexistente

## 3. Tema

- [x] 3.1 Criar o módulo de tema com a preferência `hub.tema` (`sistema`, `claro`, `escuro`), resolução pelo `matchMedia`, aplicação de `data-theme` e ouvinte de mudança do sistema, tudo com `try/catch` no armazenamento
- [x] 3.2 Em `index.html`, adicionar o script embutido no `<head>` que aplica o tema antes da primeira pintura
- [x] 3.3 Testes unitários do módulo de tema: padrão sistema, escolha persistida, sistema escuro, armazenamento indisponível, mudança do sistema com preferência sistema
- [x] 3.4 Corrigir o contraste do item ativo do menu no tema escuro (texto hoje escuro sobre realce escuro) e conferir os demais pares de cor críticos nos dois temas. Resolvido pela nova barra lateral: item ativo com `--side-ativo` e texto `--side-ink-forte`, igual nos dois temas

## 4. Casca da aplicação

- [x] 4.1 Reestruturar `index.html`: link "Pular para o conteúdo", `<header class="topbar">`, barra lateral e `<main id="view" tabindex="-1">`, mantendo `#layer`, `#login` e os ids que o código usa
- [x] 4.2 Criar o módulo da barra superior: título da tela, botão de menu, botão "+ Novo", gatilho da paleta com a dica do atalho, alternância de tema e menu do usuário
- [x] 4.3 Atualizar `Vista` em `state/nucleo.ts` com `icone?` e `acoes?: { id, rotulo, icone }[]`, e declarar ícone e ações nas telas existentes. Em vez de `icone` e `acoes` em cada `registrarVista`, os ícones e as ações rápidas ficam num catálogo único (`state/menu.ts`), junto com a estrutura em seções; `Vista` ganhou só `oculta`
- [x] 4.4 Desenhar o menu lateral com ícones, grupos recolhíveis, `aria-current` e `aria-expanded`, e acrescentar o botão de recolher com rótulos em dica e a preferência em `localStorage`
- [x] 4.5 Menu do usuário com nome, e-mail, Minha conta, Trocar senha e Sair, com Esc e clique fora para fechar e devolução do foco; mover para ele "Empresa · Papel" e "Trocar de empresa" se `multi-empresa-sessao` já estiver aplicada. "Empresa ativa" aparece no menu do usuário (nome, ou seletor quando há mais de uma empresa); o papel do usuário na empresa vem com `multi-empresa-sessao`
- [x] 4.6 Menu "+ Novo" com as ações das telas acessíveis ao usuário, teclado completo (setas, Enter, Esc) e devolução do foco
- [x] 4.7 Painel de menu no celular (até 860px): botão na barra superior, fundo escurecido, foco preso, Esc e toque fora fecham, escolher um item fecha; remover a faixa horizontal de abas de `responsive.css`
- [x] 4.8 Manter "Usando agora", sincronização e conta sempre visíveis, na barra expandida, na recolhida e no painel do celular
- [x] 4.9 Estilos da casca em `layout.css` e arquivos relacionados usando apenas tokens, nos dois temas

## 5. Paleta de comandos

- [x] 5.1 Criar a função de filtro (sem acento, sem diferença de caixa) e a montagem da lista a partir das telas visíveis e das ações rápidas, respeitando as permissões do usuário
- [x] 5.2 Criar a interface da paleta como diálogo modal com padrão de combobox e listbox (`aria-controls`, `aria-activedescendant`, `role="option"`), foco preso, setas, Enter e Esc, estado "nada encontrado" e devolução do foco
- [x] 5.3 Ligar o atalho Ctrl+K e ⌘+K (com `preventDefault`) e o gatilho da barra superior
- [x] 5.4 Executar telas pelo roteador e ações pelo registro de ações já existente (`registrarAcao`)
- [x] 5.5 Testes unitários do filtro e da montagem da lista: acento, caixa, permissões, sem resultados, ações

## 6. Navegação por URL

- [x] 6.1 Criar `state/roteador.ts` com o mapeamento de rotas (`/`, `/<vista>`, `/<vista>/novo`, `/<vista>/<id>`), as rotas reservadas (`/login`, `/login/2fa`, `/convite/…`, `/assets`, `/api`) e `registrarRotaDeRegistro(vistaId, { novo, abrir })`
- [x] 6.2 Fazer `ir(id)` usar `pushState`, tratar `popstate`, ler a rota na carga inicial, cair no painel com `replaceState` em rota desconhecida ou sem permissão, e usar a aba salva só em `/`
- [x] 6.3 Preservar sem alteração os fluxos de login, `/login/2fa` e `/convite/<token>` em `main.ts`
- [x] 6.4 Atualizar o título do documento e da barra superior conforme a rota
- [x] 6.5 Testes unitários do roteador: resolução de rotas, reservadas, desconhecida, sem permissão, raiz com aba salva, endereço explícito prevalece

## 7. Componentes de CRM

- [x] 7.1 Reestilizar `.head` e `.tools` como cabeçalho de página, e criar `cabecalhoDePagina({ titulo, descricao, trilha, acoes })` em `ui/componentes.ts`
- [x] 7.2 Reestilizar `.tbl-wrap` e `table`: cabeçalho fixo, destaque da linha, rolagem horizontal contida, linha clicável com foco visível e Enter
- [x] 7.3 Estilizar a barra de ferramentas de listagem (busca e contagem de resultados) e aplicá-la às listagens existentes. Aplicada à listagem de Clientes (busca sem acento, filtros por chip e contagem); as demais listagens mantêm a busca no cabeçalho, já com o novo visual do campo, e adotam `barraDeFerramentas` quando forem tocadas
- [x] 7.4 Reestilizar `.pill` como selos de status com texto e cor semântica nos dois temas
- [x] 7.5 Criar `estadoVazio`, `estadoDeErro` (com "Tentar de novo") e o estado de carregamento, e aplicá-los às listagens e painéis. `estadoVazio`, `estadoDeErro` e `carregando` criados e aplicados em Clientes, Minha conta, Dados da empresa e no painel (cujo esqueleto de carregamento aparecia como texto escapado)
- [x] 7.6 Reestilizar `.panel` e `.kpi` como cartões e indicadores consistentes, usando os tokens de espaçamento e raio
- [x] 7.7 Reestilizar `.btn`, `.field` e controles com as alturas de `--controle-*` e foco visível
- [x] 7.8 Remover estilos inline repetidos (`style="max-width:680px"` e similares) das telas tocadas, trocando por classes. Feito nas telas tocadas (Clientes, Minha conta, Dados da empresa); as demais seguem como estavam
- [x] 7.9 Aplicar `prefers-reduced-motion` às animações da casca, da paleta e da gaveta

## 8. Formulário em página e piloto de cliente

- [x] 8.1 Extrair o estado de registro aberto para `ui/registro-aberto.ts`, usado por `gaveta.ts`, e manter `gavetaAberta` exportado como alias
- [x] 8.2 Criar `ui/formulario-pagina.ts` com `abrirFormulario` (cabeçalho com trilha e título, seções em cartões, navegação entre seções, barra de ações fixa, exclusão em dois cliques, estado "Registro não encontrado") e os estilos correspondentes. O `render()` passa a não redesenhar a área principal enquanto o formulário está aberto (senão o WebSocket ou uma gravação o apagariam)
- [x] 8.3 Implementar o instantâneo normalizado de valores e a proteção contra perda: confirmação ao navegar, ao usar Voltar e `beforeunload` ao recarregar ou fechar
- [x] 8.4 Garantir no formulário em página o aviso de conflito de edição, o registro da versão gravada pela própria sessão e a presença "editando…", com o mesmo comportamento da gaveta. Gaveta aberta por cima de um formulário em página restaura o registro anterior ao fechar
- [x] 8.5 Criar a variante por seções de `camposDoParceiro` e `lerCamposDoParceiro` (Dados gerais, Contato, Endereço, Observações) sem alterar o uso do formulário de fornecedores
- [x] 8.6 Migrar `formCliente` para formulário em página com a seção Relacionados, as rotas `/clientes/novo` e `/clientes/<id>` e as ações atuais (salvar, WhatsApp, novo negócio e excluir)
- [x] 8.7 Atualizar a abertura de cliente nas demais telas (`data-open="cliente:…"`) para navegar pela rota do registro
- [x] 8.8 Registrar em `frontend/PADROES.md` o critério gaveta ou página e como criar um formulário em página

## 9. Testes

- [x] 9.1 Testes unitários (vitest) do instantâneo e da proteção contra perda: sem alterações, alterado, alterado e restaurado, após salvar
- [x] 9.2 Testes de `conflito.ts` e `gravacao.ts` com o estado de registro aberto movido, confirmando o comportamento anterior
- [x] 9.3 E2E de rotas: navegar atualiza a URL, Voltar e Avançar, recarregar uma tela e um registro, rota desconhecida e sem permissão, aba salva só na raiz
- [x] 9.4 E2E da casca: pular para o conteúdo, recolher a barra e lembrar, painel de menu no celular com foco preso e Esc, menu do usuário, "+ Novo"
- [x] 9.5 E2E da paleta (atalho, filtro sem acento, ir a uma tela, executar ação, sem resultados, teclado) e do tema (escolher, persistir, sem flash)
- [x] 9.6 E2E do formulário de cliente em página: abrir por link, salvar, aviso de alterações, registro inexistente, exclusão em dois cliques
- [x] 9.7 Confirmar que os e2e existentes de login, 2FA e convite continuam passando. `login-2fa.spec.ts` passa (Chromium e Firefox). O convite não tem e2e (a lógica do convite pendente tem testes unitários que passam). `fluxo-critico.spec.ts` já falhava antes: depende de backend real com usuário semeado e seu seletor `h1` é ambíguo (a tela de login tem dois `h1`); não foi alterado

## 10. Validação final

- [x] 10.1 Rodar `npm run typecheck`, `npm run lint` e `npm test`, e os e2e completos
- [x] 10.2 Gerar as capturas "depois" de todas as telas em claro, escuro e celular, compará-las com as "antes" e corrigir regressões visuais, sobreposições, texto ilegível e rolagem horizontal da página
- [x] 10.3 Verificar manualmente só com teclado a casca, a paleta, os menus e o formulário em página, e conferir o contraste AA nos dois temas
- [ ] 10.4 Conferir em produção a recarga de `/clientes/<id>` (fallback de SPA) antes de publicar
- [x] 10.5 Revisar o diff final quanto a regressões, acessibilidade e complexidade desnecessária
- [x] 10.6 Corrigir o contraste do tema claro (selos e teal abaixo de 4.5:1) com tokens de texto próprios, sem alterar a paleta de status (decisão D11)

## Context

**Casca atual.** `index.html` tem `.app` (grid de duas colunas) com `<aside>` (marca, `<nav id="nav">`, bloco de presença, indicador de sincronização e bloco de conta) e `<main id="view">`, mais `#layer` (gaveta) e `#login`. Não há `<header>`. Em telas de até 860px a barra vira uma faixa horizontal de abas.

**Telas e navegação.** `registrarVista({ id, nome, grupo, somenteAdmin, carregar, depende, desenhar })` (`state/nucleo.ts`) é o único registro; `ir(id)` troca a vista por estado em memória e salva a aba em `localStorage` (`hub.aba`). As únicas rotas por URL são `/login`, `/login/2fa` e `/convite/:token`, tratadas por `location.pathname` em `main.ts`. O backend devolve `index.html` para qualquer caminho que não seja arquivo (`app/main.py`).

**Formulários.** `ui/gaveta.ts#abrirGaveta` é o ponto central de 15 arquivos de funcionalidade. Ele concentra acessibilidade (diálogo modal, Esc, devolve o foco), exclusão em dois cliques e o estado `gavetaAberta`, lido por `ui/conflito.ts` (aviso de edição concorrente) e `ui/gravacao.ts` (versão gravada pela própria sessão), além de `observarGaveta`, que alimenta a presença "editando…" no `main.ts`.

**Estilos.** ~390 linhas de CSS em 12 arquivos, com tokens em `tokens.css` (cores, escala tipográfica, sombras). Classes compartilhadas (`.head`, `.tools`, `.panel`, `.tbl-wrap`, `.pill`, `.kpi`, `.empty`, `.btn`, `.field`) são usadas pelas 17 telas, com vários `style="…"` inline. Há `:root[data-theme="dark"]` nos tokens, mas nada na interface ou no CSS o ativa.

**Ícones e fontes.** Não há ícones. Montserrat e IBM Plex vêm de `@fontsource` (hospedadas localmente).

## Goals / Non-Goals

**Goals:**
- Uma casca de aplicação (barra superior, barra lateral com ícones, menu do usuário, paleta de comandos) que dê ao Hub a aparência e a usabilidade de um CRM.
- Rotas por URL para telas e registros, com histórico do navegador funcionando.
- Um padrão de formulário em página para formulários longos, provado no formulário de cliente.
- Vocabulário de componentes compartilhado, aplicado às telas existentes sem reescrever cada uma.
- Tema claro, escuro e do sistema, ativável pelo usuário.

**Non-Goals:**
- Mudar a paleta de cores, a API, o banco ou regras de negócio.
- Combobox de busca (change própria), busca de registros na paleta, tela de configurações, parceiros por papel.
- Migrar todos os formulários para página (só o de cliente é piloto) ou redesenhar os gráficos do painel.
- Introduzir framework de UI ou biblioteca de componentes: o projeto é TypeScript sem framework e continua assim.

## Decisions

### D1. Direção visual: CRM sóbrio, validado em mockup antes de codar
Mantém navy e turquesa e muda a forma: mais respiro e menos bordas, hierarquia tipográfica clara (Montserrat nos títulos, IBM Plex Sans no corpo), tabela como elemento principal de cada lista, cor de destaque só em ação primária e estado ativo, e a barra lateral sempre escura nos dois temas. Como o projeto não tem desenho de referência, a primeira tarefa gera mockups de três telas (casca com lista, formulário em página e paleta com tema) para aprovação; o restante só começa depois dela.

### D2. Reestilizar as classes existentes em vez de criar um segundo vocabulário
`.head`, `.panel`, `.tbl-wrap`/`table`, `.pill`, `.kpi`, `.empty` e `.btn` são reescritas no próprio lugar, de modo que as 17 telas melhoram sem mexer na marcação. Peças novas entram como helpers em `ui/componentes.ts` (`cabecalhoDePagina`, `estadoVazio`, `estadoDeErro`) e são adotadas no piloto e nas telas que forem tocadas.

**Alternativa descartada:** classes novas com prefixo e migração tela a tela. Deixaria o app com dois visuais por um longo período.
**Custo aceito:** o risco de regressão visual é de todas as telas de uma vez, mitigado pela varredura de capturas antes e depois (tarefa dedicada).

### D3. Tokens novos, sem valores soltos
Acrescenta em `tokens.css`: espaçamento (`--esp-1` a `--esp-8`, base de 4px), raios (`--r-sm`, `--r-md`, `--r-lg`, `--r-full`), camadas (`--z-topbar`, `--z-gaveta`, `--z-modal`, `--z-paleta`, `--z-toast`, substituindo os 20, 21 e 30 literais), alturas de controle (`--controle-sm`, `--controle-md`, `--controle-lg`) medidas da casca (`--topbar-h`, `--sidebar-w`, `--sidebar-w-recolhida`) e o fundo da área principal (`--canvas`: cinza-claro no tema claro, sob cartões brancos, que dá profundidade sem depender de bordas). A densidade padrão usa `--controle-md` (36px) e tabelas usam uma linha compacta própria.

### D4. Ícones: sprite SVG embutido, traçados do Lucide (ISC)
`ui/icones.ts` guarda os traçados de ~30 ícones e injeta um único `<svg>` com `<symbol id="i-…">` no corpo na inicialização. `icone(nome, { rotulo? })` devolve `<svg class="ico" aria-hidden="true" focusable="false"><use href="#i-nome"/></svg>`, ou com `role="img"` e `aria-label` quando o ícone carrega sentido sozinho. `botaoIcone(nome, rotulo)` exige o rótulo. Os traçados são copiados do Lucide, com a atribuição da licença ISC no cabeçalho do arquivo. Não entra dependência de runtime.

**Alternativa descartada:** pacote de ícones como dependência. Aumenta o bundle e a superfície de dependências por ~30 ícones.
**Alternativa descartada:** `<svg>` completo em cada uso. Duplica marcação em todas as telas.

### D5. Casca com pontos de referência
`index.html` ganha `<header class="topbar" role="banner">` e o link "Pular para o conteúdo". A barra superior contém, da esquerda para a direita: botão de menu (celular), título da tela (a trilha de um registro fica no cabeçalho da própria página), botão "+ Novo" (menu de ações rápidas), gatilho da paleta com a dica `Ctrl K`, alternância de tema e menu do usuário (nome, e-mail, Minha conta, Trocar senha, Sair). A barra lateral ganha ícone por item (`Vista.icone`) e botão de recolher, que a deixa só com ícones e rótulos em dica (`title` e `aria-label`); a preferência fica em `localStorage`. No celular, a barra lateral vira um painel sobreposto com fundo escurecido, foco preso e Esc para fechar, substituindo a faixa horizontal de abas. Os blocos "Usando agora", sincronização e conta continuam na barra lateral e permanecem sempre visíveis, como exige `scrollable-sidebar-menu`.

Com `multi-empresa-sessao` aplicada, "Empresa · Papel" e "Trocar de empresa" passam do bloco de conta para o menu do usuário. Sem ela, esse menu mostra nome e e-mail.

### D6. Paleta de comandos, só local
Abre com Ctrl+K ou ⌘K (com `preventDefault` do atalho do navegador) e pelo gatilho da barra. Lista as telas visíveis ao usuário (as mesmas do menu, respeitando permissões) e as ações rápidas. Ação rápida é um id do registro de ações já existente (`registrarAcao`); `Vista.acoes` declara quais ações uma tela expõe (`{ id, rotulo, icone }`), e o "+ Novo" da barra usa a mesma lista. A busca ignora acento e caixa. Implementa o padrão ARIA de combobox com lista (`role="combobox"`, `aria-controls`, `aria-activedescendant`, `role="listbox"` e `role="option"`) dentro de um diálogo modal com foco preso, Esc para fechar e devolução do foco.

**Alternativa descartada:** buscar registros (clientes, negócios…) já na paleta. Exige endpoints de busca e o combobox assíncrono, que vêm na change própria; a paleta já fica pronta para receber esse grupo depois.

### D7. Roteamento por URL com History API
Novo `state/roteador.ts`. Mapa de rotas:

```
 /                  → última aba salva (ou painel)
 /<vista>           → tela (id de registrarVista, ex.: /clientes, /fin-titulos)
 /<vista>/novo      → formulário em página novo (se a tela registrar)
 /<vista>/<id>      → formulário em página do registro
 reservadas, fora do roteador: /login, /login/2fa, /convite/:token, /assets, /api
```

`ir(id)` passa a fazer `pushState`; `popstate` renderiza a rota; a carga inicial lê `location.pathname`; rota desconhecida cai no painel com `replaceState`. A aba salva em `localStorage` vale só para `/`. Uma tela registra suas rotas de registro com `registrarRotaDeRegistro(vistaId, { novo, abrir })`. O fallback de SPA do backend já cobre os caminhos aninhados; o deploy de produção precisa ser conferido (tarefa).

**Alternativa descartada:** roteamento por hash (`#/clientes`). Funciona sem fallback no servidor, mas não é a convenção atual das rotas `/convite/:token` e `/login`, e produz links feios.

### D8. Formulário em página: mesmo contrato da gaveta, outro contêiner
`ui/formulario-pagina.ts#abrirFormulario({ titulo, trilha, secoes, rodape, registro, autoria, montar, aoFechar })` desenha dentro de `#view`: cabeçalho com trilha, título e estado (versão, "cadastrado por…"), seções em cartões com navegação lateral por âncoras no desktop, e barra de ações fixa (Salvar, Cancelar, ações do registro e Excluir com confirmação em dois cliques, o mesmo comportamento da gaveta). O estado de "registro aberto" sai de `gaveta.ts` para `ui/registro-aberto.ts`, usado pela gaveta e pelo formulário em página; `gavetaAberta` continua exportado como alias, para que `conflito.ts`, `gravacao.ts` e a presença (`observarGaveta`) funcionem sem alteração de comportamento.

Proteção contra perda: ao montar, guarda um instantâneo normalizado dos valores; ao navegar (menu, Voltar, paleta) com alterações pendentes, pede confirmação; `beforeunload` cobre recarregar e fechar a aba. Salvar com sucesso limpa o instantâneo. Se a rota de registro for aberta direto e o registro não estiver carregado, mostra o estado "Registro não encontrado" com link de volta.

Regra de escolha: gaveta para edição curta (até ~8 campos e sem listas relacionadas); página para formulários longos, com seções ou listas relacionadas.

**Piloto, cliente:** o formulário vira página com as seções Dados gerais, Contato, Endereço, Observações e Relacionados (negócios, orçamentos, faturamento), reaproveitando `camposDoParceiro` e `lerCamposDoParceiro` (que ganha uma variante por seções, sem alterar o uso atual do formulário de fornecedores, que segue na gaveta).

**Alternativa descartada:** modal centralizado. Resolve a largura, mas não dá URL, nem seções, nem comporta listas relacionadas.

### D9. Tema: três estados, aplicado antes da pintura
Preferência `hub.tema` ∈ `sistema` (padrão), `claro`, `escuro` em `localStorage`. Um script embutido no `<head>` resolve o tema e define `data-theme` antes da primeira pintura (sem flash); a barra superior alterna entre os três estados, e um ouvinte de `matchMedia("(prefers-color-scheme: dark)")` acompanha o sistema quando a preferência é `sistema`. `localStorage` indisponível não impede o funcionamento (cai no tema do sistema).

### D10. Acessibilidade como requisito
Pontos de referência (`header`, `nav`, `main`), link para pular ao conteúdo, foco visível em tudo, diálogos com foco preso e devolução do foco, nomes acessíveis em botões só com ícone, `aria-current` no item ativo, `aria-expanded` nos recolhíveis, contraste mínimo AA nos dois temas e animações desligadas sob `prefers-reduced-motion`. Corrige de passagem o texto escuro do item ativo do menu no tema escuro, hoje com baixo contraste.

### D11. Tokens de texto para status e destaque (contraste AA)
Medindo o contraste dos pares de cor, o tema claro falhava: texto de selos ok, aviso, erro e info entre 2,5:1 e 4,2:1, e o teal sobre fundo claro em 3,7:1; o escuro passava em tudo. Em vez de alterar as cores de status (que fazem parte da paleta aprovada e arquivada), entram cinco tokens de **texto**, escurecidos o mínimo necessário só no tema claro (`--ok-texto`, `--warn-texto`, `--bad-texto`, `--info-texto`, `--teal-texto`; no escuro apontam para as cores atuais). Toda declaração `color:` que usava as cores de status passa a usar esses tokens; bordas, barras e pontos mantêm as cores originais.

**Alternativa descartada:** escurecer `--ok`, `--warn`, `--bad` e `--info` na raiz. Mudaria bordas, barras de funil e gráficos que hoje seguem a paleta aprovada.

## Risks / Trade-offs

- **[Regressão visual nas 17 telas ao reestilizar no lugar]** → Varredura de capturas de todas as telas, antes e depois, em claro, escuro e celular; reestilização em etapas por arquivo CSS, com revisão a cada uma.
- **[Rotas aninhadas em produção]** O backend já faz fallback de SPA, mas o deploy pode usar outra configuração. → Tarefa para conferir recarregar em `/clientes/<id>` no ambiente de produção antes de publicar.
- **[Roteamento mexe no bootstrap]** Rotas reservadas (`/login`, `/login/2fa`, `/convite/…`) e o fluxo de login precisam continuar intactos. → Lista de rotas reservadas explícita, testes e2e dos fluxos de login, 2FA e convite existentes.
- **[Aviso de alterações não salvas com falso positivo]** → Compara valores normalizados, só vale em formulário em página, e é coberto por testes.
- **[Atalho Ctrl+K colide com o navegador]** → `preventDefault` apenas quando a aplicação está ativa e o foco não está num campo de texto de outra origem; o gatilho visível na barra é o caminho garantido.
- **[Mover o estado da gaveta quebra conflito e presença]** → Alias `gavetaAberta` mantido e testes de `conflito.ts` e `gravacao.ts` antes e depois.
- **[Gosto visual é subjetivo]** → Mockups aprovados antes de codar (D1).
- **[Ordem com `multi-empresa-sessao`]** Ambas mexem no bloco de conta e no bootstrap de `main.ts`. → Aplicar esta depois; a migração de "Empresa · Papel" para o menu do usuário é um passo condicional.
- **[Licença dos ícones]** → Atribuição ISC no cabeçalho de `ui/icones.ts`.

## Migration Plan

1. Aprovar os mockups (tarefa 1) e registrar a decisão.
2. Entregar em etapas que deixam o app funcional a cada uma: tokens e ícones; tema; casca; paleta; roteador; componentes; formulário em página com o piloto.
3. Antes de publicar: varredura visual, e2e completo (incluindo login, 2FA e convite) e a conferência do fallback de SPA em produção.
4. **Rollback:** a mudança é só de frontend; reverter o deploy restaura o comportamento anterior. Preferências novas em `localStorage` (`hub.tema`, barra recolhida) são ignoradas pela versão antiga.

## Open Questions

- Os mockups da tarefa 1 precisam da sua aprovação antes do restante; é um ponto de parada deliberado.
- Além de Clientes, qual formulário migra em seguida para página? Orçamentos (tabela de itens) é o candidato mais forte, mas fica para a próxima change.
- A barra lateral inicia expandida por padrão, e só lembra o recolhimento depois que o usuário o escolhe. Alguma preferência diferente?

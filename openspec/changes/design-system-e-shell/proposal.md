## Why

O Hub funciona, mas ainda parece um conjunto de formulários densos e não um CRM profissional:

- **Não há estrutura de aplicação:** sem barra superior, sem ícones, com menu só de texto e sem lugar para busca, ação rápida, tema ou menu do usuário.
- **Todo formulário abre numa gaveta lateral de 640px** (15 arquivos chamam `abrirGaveta`), inclusive os de muitos campos e listas relacionadas, como o de cliente.
- **Nenhuma tela ou registro tem URL própria:** a navegação é por estado em memória, então não há link compartilhável, o botão Voltar do navegador não ajuda e recarregar devolve à última aba salva.
- **O tema escuro existe nos tokens, mas ninguém consegue ativá-lo:** não há botão de alternância nem regra de `prefers-color-scheme` (a spec `theme-system` já exige as duas coisas).
- **Faltam peças de interface compartilhadas:** cabeçalho de página, barra de ferramentas de tabela, estados vazio e de erro e cartões repetem estilos inline (`style="max-width:680px"`), o que impede um visual consistente.

A paleta de cores (azul-marinho e turquesa) foi aprovada e permanece. Esta change cria a camada de design system e a casca da aplicação sobre a qual as demais changes (combobox, configurações, parceiros por papel) vão se apoiar.

## What Changes

- **Casca da aplicação:** barra superior (título da tela, ação "+ Novo", paleta de comandos, alternância de tema e menu do usuário) e barra lateral com ícones, recolhível a só ícones (preferência lembrada). No celular, o menu vira um painel acionado por botão, no lugar da faixa horizontal de abas.
- **Paleta de comandos (Ctrl/⌘+K):** navegar para qualquer tela e executar ações rápidas ("Novo cliente", "Novo orçamento"…), com busca sem acento e teclado completo. Não busca registros; isso fica para depois do combobox.
- **Ícones:** conjunto próprio de ícones SVG embutidos (sem dependência nova de runtime), usados no menu, nos botões e nos estados.
- **Navegação por URL:** cada tela tem rota (`/clientes`, `/fin-titulos`…) e os formulários em página têm rota de registro (`/clientes/<id>`, `/clientes/novo`), com Voltar, Avançar, recarregar e links compartilháveis funcionando.
- **Formulário em página:** novo padrão para formulários longos, com seções, navegação entre seções, barra de ações fixa, aviso de alterações não salvas e URL própria. A gaveta continua para edições curtas. **Piloto: o formulário de cliente.**
- **Componentes de CRM** (aplicados por reestilização das classes atuais, para que as 17 telas melhorem sem reescrever marcação): cabeçalho de página, barra de ferramentas de tabela, tabela com cabeçalho fixo, selos de status, estados vazio, de erro e de carregamento, cartões e indicadores.
- **Tema:** alternância Sistema, Claro e Escuro na barra superior, persistida, aplicada antes da pintura (sem flash) e respeitando `prefers-color-scheme`.
- **Tokens:** escalas de espaçamento, raio, camadas (z-index), alturas de controle e densidade, além dos já existentes.
- **Acessibilidade:** pontos de referência (`header`, `nav`, `main`), link "pular para o conteúdo", foco visível, atalhos sem armadilha de teclado, respeito a `prefers-reduced-motion`.
- **Direção visual validada antes de codar:** mockups de três telas para sua aprovação (tarefa inicial desta change), já que não há desenho de referência.

Não muda: API, banco, regras de negócio e a paleta de cores. Nenhuma mudança **BREAKING** de contrato; o comportamento de URL, Voltar e recarregar muda para melhor.

Fora de escopo: combobox com busca (change própria), busca de registros na paleta, tela de configurações, parceiros por papel, redesenho dos gráficos do painel e migração de todos os formulários para página (só o de cliente é piloto).

## Capabilities

### New Capabilities
- `app-shell`: barra superior, barra lateral com ícones e recolhimento, menu móvel, menu do usuário, ação "+ Novo" e paleta de comandos.
- `icones-ui`: conjunto de ícones SVG embutidos e a forma de usá-los com acessibilidade.
- `componentes-crm`: cabeçalho de página, barra de ferramentas e tabela de dados, selos de status, estados vazio, de erro e de carregamento, cartões e indicadores.
- `formulario-em-pagina`: padrão de formulário em página com seções, barra de ações fixa, proteção contra perda de alterações e URL de registro; critério de quando usar gaveta ou página.
- `navegacao-por-url`: rotas por tela e por registro, histórico do navegador, recarga e rotas reservadas.

### Modified Capabilities
- `design-system-tokens`: novos tokens de espaçamento, raio, camadas, alturas de controle e densidade.
- `theme-system`: alternância manual de tema na interface, persistência e aplicação sem flash.
- `scrollable-sidebar-menu`: a largura de 272px passa a valer com a barra expandida, e a barra recolhida tem largura reduzida.

## Impact

- **Frontend:** `index.html` (nova estrutura da casca e script de tema), `main.ts`, `state/nucleo.ts` (roteamento e menu), `ui/gaveta.ts` e módulos que leem `gavetaAberta` (`ui/conflito.ts`, `ui/gravacao.ts`), novos módulos de casca, ícones, paleta, roteador e formulário em página, `features/clientes.ts` (piloto), todos os CSS de `styles/` (reestilização), `frontend/PADROES.md`.
- **Backend e banco:** nenhum. O fallback de SPA já devolve `index.html` para caminhos aninhados (`app/main.py`); falta confirmar o mesmo no deploy de produção.
- **Dependências novas:** nenhuma de runtime. Os ícones usam traçados do Lucide (licença ISC) copiados com atribuição.
- **Testes:** vitest para roteador, filtro da paleta, proteção de alterações e preferência de tema; e2e para URL e Voltar, formulário em página, paleta, tema e recolhimento; varredura de capturas de tela das telas antes e depois, em claro, escuro e celular.
- **Dependência de ordem:** deve ser aplicada **depois** de `multi-empresa-sessao`. Quando ela existir, o seletor "Empresa · Papel" e "Trocar de empresa" passam da barra lateral para o menu do usuário na barra superior; se ainda não existir, o menu do usuário mostra só nome e e-mail.

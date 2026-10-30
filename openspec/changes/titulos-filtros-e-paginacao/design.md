# Design

## Context

- `servicos.listar_titulos` monta a consulta com `_consulta_titulos` (`joinedload` de conta bancária, plano e parceiro;
  relações são `lazy="raise"`), aplica `tipo`, `status`, `de`, `ate` e `busca` (join em `Parceiro`) e devolve tudo.
- A tela (`features/financeiro/titulos.ts`) chama `apiFinanceiro.titulos.listar()` sem filtros, filtra por `ui.finTipo`
  e `ui.finStatus` no cliente e soma "em aberto" sobre a lista inteira.
- Não existe paginação em nenhuma rota nem componente de paginação. O roteamento do frontend é por `location.pathname`;
  não lê nem grava query string.
- Ordem de grandeza: centenas de títulos por empresa. Uso: triagem semanal.

## Goals / Non-Goals

**Goals:**
- Um único ponto de montagem do filtro, usado pela listagem, pelos totais e pela exportação.
- Totais do cabeçalho coerentes com o filtro, independentes da página.
- Estado da listagem recuperável pela URL.

**Non-Goals:**
- Paginação por cursor (centenas de registros não justificam).
- Filtros salvos com nome, por usuário.
- Exportar para XLSX ou PDF; escolher colunas do CSV.
- Aplicar o mesmo padrão a outras listas (fica como evolução).

## Decisions

### 1. Filtro, ordenação e paginação no servidor
Mesmo com centenas de linhas, o servidor é quem sabe o total e os totais por tipo; mantê-los no cliente obrigaria a
baixar tudo para paginar. `limit`/`offset` (`pagina`, `tamanho` ∈ {25, 50, 100}) bastam.
Alternativa descartada: paginar só na tela. Mais barata, mas deixa o payload crescer sem limite e não serve à exportação.

### 2. Uma função de filtro, três usos
`_filtrar_titulos(empresa, filtros) -> Select` aplica todos os filtros sem ordenar nem limitar. Em cima dela:
- listagem: `order_by` + `limit/offset`;
- `total`: `select(count()).select_from(filtro.subquery())`;
- `totais`: `SUM(valor_devido)` por `tipo_conta` só dos `status = 'A'` do filtro;
- exportação: mesma ordenação, sem `limit`.
`valor_devido` não é coluna: é `valor_titulo - valor_desconto + valor_multa + valor_juros`. Vira uma expressão SQL
compartilhada (usada em soma, faixa de valor e ordenação), equivalente a `regras.valor_devido`. Um teste compara as duas.
Os filtros de parceiro por nome (`busca`) e por id coexistem. O join em `Parceiro` é feito uma vez, quando preciso
(`busca` ou ordenação por parceiro), para evitar duplicar a junção.

### 3. Envelope de resposta
`{itens: TituloLeitura[], total: int, totais: {a_receber, a_pagar}}`. `totais` considera só títulos abertos do filtro
(o que o cabeçalho mostra hoje). Alternativa descartada: totais em rota separada, que custaria uma segunda chamada a
cada mudança de filtro. O consumidor conhecido é só a tela de títulos (`api.ts`) e o `e2e/financeiro.mjs`, então a
quebra de contrato é contida.

### 4. Ordenação
`ordem` ∈ {`vencimento`, `valor`, `parceiro`} e `sentido` ∈ {`asc`, `desc`}. Sempre com desempate por
`created_at, id`, para a página não repetir nem pular linhas. Padrão: vencimento crescente (comportamento atual).

### 5. "Atrasados" e "próximos 7 dias"
São atalhos da tela, não parâmetros novos do negócio: "Atrasados" envia `status=A` e `ate=ontem`; "Próximos 7 dias"
envia `status=A`, `de=hoje`, `ate=hoje+6`. "Hoje" é a data do navegador, como em `hoje()`. A API só conhece intervalos,
o que a mantém simples e testável. O filtro "recorrente ou avulso" é `recorrente: bool | None`.
Alternativa descartada: um parâmetro `atrasados=true` no servidor. Duplicaria a regra de data e dependeria do fuso.

### 6. Exportação CSV
`GET /financeiro/titulos/exportar` com os mesmos parâmetros de filtro (menos a paginação), resposta
`text/csv; charset=utf-8` com BOM, separador `;`, decimal com vírgula e data `dd/mm/aaaa`, para abrir direto no Excel
em português. Colunas: vencimento, tipo, parceiro, conta do plano, conta bancária, valor do título, desconto, multa,
juros, valor devido, situação, data de pagamento, valor pago, anotação. Campos de texto que começam com `=`, `+`, `-` ou
`@` recebem apóstrofo, contra injeção de fórmula. O limite de linhas é 10.000, com cabeçalho de aviso se atingido.
A tela baixa por requisição autenticada (`fetch` + `Blob`), já que o token não vai em link simples.

### 7. Estado na URL
Query string com chaves curtas e só valores diferentes do padrão (`/fin-titulos?status=A&venc_ate=2026-11-07&pag=2`).
Alterar filtro ou ordem usa `history.replaceState` e zera a página; trocar de página usa `pushState`, para o Voltar
funcionar entre páginas. Ao abrir a URL, o estado é lido antes do primeiro `carregar`. Valores inválidos são ignorados.
Os botões Tipo e Situação passam a escrever na URL em vez de só em `ui.finTipo`/`ui.finStatus`.
Hoje o roteamento só olha `pathname`, então a leitura e a escrita da query string viram uma pequena camada comum
(`state/consulta-url.ts`), reaproveitável por outras listas.

### 8. Gaveta de filtros
Usa `abrirGaveta` e os comboboxes existentes (parceiro, conta do plano, conta bancária). Botão "Aplicar" grava na URL e
recarrega; "Limpar" zera os avançados. O rótulo "Filtros (n)" conta só os campos da gaveta. Cada filtro ativo também
vira um chip removível acima da tabela, inclusive os dos atalhos.

### 9. Desempenho
Com centenas de linhas, nenhum índice novo é necessário agora. A consulta já filtra por `empresa_id`; se crescer, um
índice `(empresa_id, data_vencimento)` é uma migração isolada. Fica registrado, sem fazer.

## Risks / Trade-offs

- **Quebra de contrato do `GET /titulos`** → único consumidor é a tela (e o e2e); atualizar os dois na mesma mudança.
- **Expressão de `valor_devido` duplicada em SQL e Python** → teste que compara as duas sobre os mesmos dados.
- **Página fora do intervalo** (título excluído, filtro mais estreito) → servidor devolve a lista vazia com `total`; a
  tela volta para a última página válida.
- **Fuso de "hoje"** → os atalhos usam a data local do navegador, como o resto da tela.
- **CSV aberto no Excel** → BOM, `;` e vírgula decimal, além do escape de fórmulas.

## Open Questions

- A semana de "Vence nos próximos 7 dias" é de hoje a hoje+6 (assumido aqui), não segunda a domingo. Confirmar.

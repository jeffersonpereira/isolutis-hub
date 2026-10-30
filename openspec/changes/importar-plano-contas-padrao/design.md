# Design

## Context

- `plano_contas` tem `empresa_id` (RLS), `plano_pai_id`, `codigo`, `nome`, `tipo_conta` (`A`/`S`), `natureza`,
  `nivel` e `aporte_socio`. O trigger `tg_plano_contas_regras` (RN01) calcula nível e natureza a partir do pai e valida
  o código; `uq_plano_contas_empresa_codigo` impede códigos repetidos na empresa.
- O plano padrão está em `backend/app/financeiro/dados/plano_contas_padrao.csv` (149 contas; colunas `id`,
  `plano_pai_id`, `codigo`, `nome`, `tipo_conta`, `natureza`). Os `id` são fixos e a chave primária de `plano_contas` é
  global, por isso o script do operador só serve para uma empresa por banco.
- A tela `fin-plano` já tem um estado vazio ("Plano de contas vazio … Criar a primeira conta").
- Rotas `/financeiro/*` exigem a permissão `financeiro` (`requer_financeiro`) e passam pela idempotência; o `admin`
  tem essa permissão. Gravações em `plano_contas` já publicam o recurso `financeiro` no tempo real.

## Goals / Non-Goals

**Goals:**
- Qualquer empresa sem contas pode importar o plano padrão pela aplicação, quantas empresas forem.
- Operação atômica e segura contra cliques duplos e duas pessoas importando ao mesmo tempo.

**Non-Goals:**
- Planos por segmento da empresa ou editor do plano padrão pelo operador (o CSV versionado continua sendo a fonte).
- Prévia da árvore antes de importar (há só a confirmação), importação parcial ou mesclagem com plano existente.
- Aviso no painel/alertas, passo no onboarding ou aviso ao criar título sem plano (podem vir depois).
- Mudar o script `carregar_plano_contas.py`.

## Decisions

### 1. O CSV vira só estrutura; os ids são gerados na importação
Os `id` do CSV servem apenas como chave para ligar filho ao pai. A importação cria um `uuid4` por conta, monta o mapa
`id do CSV → id novo` e grava `plano_pai_id` pelo mapa. Assim nenhuma empresa ocupa os ids de outra.
Alternativa descartada: trocar os ids do CSV por códigos. Mexeria no arquivo que o script do operador também lê.

### 2. Só com o plano vazio, conferido no servidor
`importar_plano_padrao` conta as contas da empresa e recusa com `Conflito` (409, "A empresa já tem plano de contas")
se houver alguma. Para não depender só da contagem, a transação toma `pg_advisory_xact_lock` por empresa antes de
contar; se mesmo assim a restrição `uq_plano_contas_empresa_codigo` disparar numa corrida, o erro vira o mesmo 409.
Alternativa descartada: `SELECT … FOR UPDATE` na linha da empresa, que exige o privilégio de UPDATE (só admin) e
quebraria para o papel `financeiro`.

### 3. Inserção em ordem de nível, numa transação
Inserir por nível (1, 2, 3) para o pai existir antes do filho; nível e natureza continuam vindo do trigger (RN01), sem
duplicar a regra no Python. Qualquer falha desfaz tudo (nunca existe plano pela metade).

### 4. `aporte_socio` por código
A conta `7.02.001` ("Aportes de Capital") é gravada com `aporte_socio = true`, como o script do operador já faz, para
o fluxo de sócios funcionar sem ajuste manual. A constante fica num só lugar, compartilhada com a leitura do plano.

### 5. Leitura e validação do CSV em módulo próprio
`financeiro/plano_padrao.py` lê o CSV uma vez (cache em memória) e valida ids/códigos repetidos e pais ausentes, com a
mesma lógica de `carregar_plano_contas.ler_plano`. Não importamos o script (ele é de operador e tem efeitos de
console); a duplicação é pequena e o teste cobre o CSV real.

### 6. Rota e permissão
`POST /financeiro/plano-contas/importar-padrao`, no router `financeiro` (permissão `financeiro`, idempotência
herdada). Responde 201 com a lista de `PlanoContaLeitura` já ordenada, para a tela se atualizar sem nova ida ao
servidor.

### 7. Frontend
No estado vazio de `plano-contas.ts`, um segundo botão "Importar plano padrão" abre a janela de confirmação
(`ui/confirmar`) com o texto "Cria o plano de contas padrão, em três níveis. Depois você pode editar, incluir e excluir contas livremente" (sem o número de contas, para não envelhecer com o CSV). Depois
da resposta, a tela recarrega o recurso `financeiro` e mostra um aviso. Em caso de 409 (outra pessoa importou antes), a
tela só recarrega e mostra a mensagem.

## Risks / Trade-offs

- **Plano genérico demais** (hoje reflete uma empresa de software) → o texto da confirmação avisa que é editável; planos
  por segmento ficam para depois, com o desenho aberto (a fonte é um arquivo, trocável por escolha de arquivo).
- **Duas pessoas importando juntas** → advisory lock + restrição de unicidade; a segunda recebe 409 sem efeito.
- **Duplicação da leitura do CSV** → coberta por teste que lê o arquivo real e confere 149 contas, pais válidos e uma
  única conta de aporte.

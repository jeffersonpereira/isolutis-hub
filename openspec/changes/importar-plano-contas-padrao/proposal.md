# Proposal

## Why

Uma empresa recém-cadastrada nasce sem plano de contas, e sem ele o módulo financeiro não funciona (títulos,
recorrências, relatórios e aportes de sócios dependem de contas). Hoje a pessoa precisa criar as contas uma a uma, ou
pedir ao operador que rode um script de terminal (`carregar_plano_contas.py`) que ainda por cima **apaga** o plano
existente e usa ids fixos, o que só permite o plano padrão em uma empresa por banco. O produto é um SaaS
multiempresa: a importação do plano padrão precisa estar na própria aplicação e funcionar para qualquer empresa.

## What Changes

- Nova ação **"Importar plano padrão"** na tela Plano de contas, exibida quando a empresa não tem nenhuma conta, ao
  lado de "Criar a primeira conta", com confirmação antes de importar.
- Nova rota `POST /financeiro/plano-contas/importar-padrao`: cria as 149 contas do plano padrão (3 níveis) para a empresa
  ativa, numa só transação, com **ids novos** a cada importação, e devolve o plano criado.
- A importação **só é aceita com o plano vazio**: se a empresa já tem alguma conta, a API recusa (conflito) e nada é
  alterado. Nunca apaga nem sobrescreve contas.
- A conta de aporte de sócios (`7.02.001`) já nasce marcada como `aporte_socio`.
- Permissão `financeiro` (o `admin` também tem), a mesma das demais rotas do módulo.

## Capabilities

### New Capabilities
- `importar-plano-contas-padrao`: oferta e execução da importação do plano padrão para empresa sem plano de contas
  (condição de vazio, atomicidade, ids novos, aporte de sócio, permissão, isolamento por empresa).

### Modified Capabilities
- `plano-contas-view`: o estado vazio da tela passa a oferecer a importação do plano padrão.

## Impact

- **Backend**: novo `financeiro/plano_padrao.py` (leitura e validação do CSV `dados/plano_contas_padrao.csv`) e
  `servicos.importar_plano_padrao`; nova rota em `financeiro/rotas.py`. Sem migração de banco.
- **Frontend**: `features/financeiro/api.ts` e `features/financeiro/plano-contas.ts` (botão, confirmação, recarga).
- **Script existente** `carregar_plano_contas.py`: continua como ferramenta do operador (substituição de plano, ids
  fixos); não é alterado nesta mudança.
- **Dados existentes**: nenhum. Empresas com plano não veem a opção.

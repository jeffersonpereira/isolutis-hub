## Why

A máscara monetária "estilo caixa eletrônico" (`ui/moeda.ts`, `mascara-monetaria`) embaralha o valor ao digitar normalmente, tecla a tecla, em qualquer campo de valor em reais (título, negócio, produto, conta bancária, recorrência, faturamento). Reproduzido na tela de Títulos: digitar `132,20` tecla a tecla resulta em `3.022,01`. A causa é o reposicionamento de cursor em `reaplicarMascara` (`ui/mascara.ts`), que conta "dígitos antes do cursor" sem diferenciar dígitos realmente digitados de zeros de preenchimento que `formatarCentavos` insere (via `padStart(3, "0")`) quando o valor tem menos de 3 dígitos — por isso o cursor para antes do fim do campo e a tecla seguinte entra no meio da sequência de dígitos em vez de no fim, deslocando o valor a cada tecla subsequente. Isso torna praticamente impossível digitar um valor monetário corretamente em qualquer tela do sistema, sendo um bug bloqueante introduzido pela feature `mascara-monetaria` (hoje).

## What Changes

- Corrige o reposicionamento de cursor usado pela máscara monetária para sempre ancorar no fim do campo após cada tecla, já que nesse tipo de máscara ("dígitos entram pela direita como centavos") não existe "o mesmo dígito" de uma formatação para a seguinte — a posição relativa do dígito mais à esquerda é redefinida a cada tecla, então preservar uma posição de cursor no meio do campo nunca é correto.
- Mantém intacto o comportamento de `reaplicarMascara` para a máscara de documento (CPF/CNPJ, `ui/documento.ts`), que continua precisando preservar a posição relativa do cursor (formato fixo, sem dígitos de preenchimento reinterpretados) — ou seja, as duas máscaras passam a ter estratégias de cursor diferentes, cada uma correta para o seu próprio formato.
- Adiciona teste automatizado que simula digitação tecla a tecla (múltiplos eventos `input` em sequência, com o cursor avançando a cada um, como o navegador realmente dispara) no campo monetário, cobrindo o caso relatado (`132,20` dígito a dígito) — os testes atuais só verificam a máscara aplicada de uma vez (valor final atribuído e um único evento disparado), por isso não capturaram o bug.

## Capabilities

### New Capabilities
_Nenhuma._

### Modified Capabilities
- `mascara-monetaria`: o requisito de digitação passa a exigir que, ao digitar tecla a tecla do início ao fim do valor (sem editar no meio de um valor já preenchido), o resultado final seja o valor correto correspondente à sequência de dígitos digitada — não só quando o valor é atribuído de uma vez.

## Impact

- **Frontend (`frontend/src`)**:
  - Alterado: `ui/mascara.ts` (estratégia de reposicionamento de cursor; precisa diferenciar o caso "moeda" do caso "documento", ou cada máscara passa a ter sua própria lógica de cursor).
  - Alterado: `ui/moeda.ts` (ajusta a chamada a `reaplicarMascara`/nova função de reposicionamento, se a assinatura mudar).
  - Novo/alterado: `ui/mascara.test.ts` ou `ui/moeda.test.ts` (teste de digitação tecla a tecla).
  - Sem impacto em `ui/documento.ts` além de garantir que seu comportamento atual (testado em `ui/documento.test.ts`) continua intacto.
- **Backend**: nenhum impacto — bug é só de apresentação/digitação no frontend.
- **Alcance do bug**: todo campo criado com `inpMoeda` (`ui/campos.ts`) em qualquer tela — títulos, negócios, produtos, contas bancárias, recorrências, faturamento, itens de orçamento, onboarding.

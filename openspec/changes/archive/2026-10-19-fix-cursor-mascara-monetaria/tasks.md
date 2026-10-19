## 1. Nova estratégia de cursor em `ui/mascara.ts`

- [x] 1.1 Adicionar `reaplicarMascaraAoFim(campo, mascarar)`: remascara o valor e, se o campo ainda estiver com foco, reposiciona o cursor sempre no fim do valor remascarado (`novo.length`), em vez de preservar a posição relativa do dígito.
- [x] 1.2 Manter `reaplicarMascara` (contagem de dígitos antes do cursor) inalterada — continua sendo usada por `ui/documento.ts`.

## 2. Ligar a nova estratégia na máscara monetária

- [x] 2.1 Atualizar `ligarMascaraDeMoeda` em `ui/moeda.ts` para chamar `reaplicarMascaraAoFim` em vez de `reaplicarMascara`.

## 3. Testes

- [x] 3.1 Em `ui/moeda.test.ts`, adicionar teste que simula digitação tecla a tecla: para cada dígito de `13220`, inserir o caractere na posição do cursor, disparar `input`, e repetir — assert que o valor final é `132,20` (reproduz o caso relatado: `132,20` digitado tecla a tecla hoje resulta em `3.022,01`).
- [x] 3.2 Adicionar teste equivalente para um valor menor que 3 dígitos digitado tecla a tecla (ex.: `5`, `0` → `0,50`), já que é o caso onde o padding de `formatarCentavos` mais interfere.
- [x] 3.3 Confirmar que `ui/documento.test.ts` continua passando sem alteração (garante que `reaplicarMascara`/máscara de CPF/CNPJ não regrediu).

## 4. Validação manual

- [x] 4.1 Rodar a suíte de testes do frontend (`npm test` / `vitest`) e confirmar que tudo passa, incluindo os novos testes.
- [x] 4.2 Testar manualmente na tela de Títulos: abrir "Novo título", digitar `132,20` tecla a tecla no campo "Valor do título" e confirmar que o campo exibe `132,20` ao final.
- [x] 4.3 Testar manualmente a edição de um título existente (campo monetário já preenchido) para confirmar que digitar mais dígitos ao final continua funcionando e que o comportamento ao editar no meio do valor é o esperado (cursor vai para o fim, conforme decisão de design).

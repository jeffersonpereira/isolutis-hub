## Context

`ui/mascara.ts` tem uma única função, `reaplicarMascara(campo, mascarar)`, reaproveitada por duas máscaras com formatos fundamentalmente diferentes:

- **Documento** (`ui/documento.ts`, CPF/CNPJ): formato de tamanho fixo, onde cada dígito digitado continua sendo "o mesmo dígito" antes e depois de formatar — só pontuação (`.`, `-`, `/`) é inserida entre eles. Preservar a posição relativa do cursor contando dígitos faz sentido aqui.
- **Moeda** (`ui/moeda.ts`, `mascararMoeda`/`formatarCentavos`): os dígitos digitados entram sempre pela direita como centavos; a cada tecla, o número inteiro é reconstruído a partir de todos os dígitos em sequência, e `formatarCentavos` ainda insere zeros de preenchimento (`padStart(3, "0")`) quando há menos de 3 dígitos. Não existe "o mesmo dígito" de uma formatação para a seguinte: a tecla digitada sempre deveria terminar no fim do campo, nunca no meio.

`reaplicarMascara` conta "quantos dígitos existem antes do cursor" no valor anterior e tenta achar a posição equivalente no valor novo. Para moeda, essa contagem inclui os zeros de preenchimento (que não foram digitados por ninguém), então o cursor para antes do fim do campo — e a tecla seguinte entra no meio da sequência de dígitos, deslocando o valor. Reproduzido: digitar `1`,`3`,`2`,`2`,`0` tecla a tecla (5 eventos `input`, como o navegador realmente dispara, cursor avançando a cada um) termina em `3.022,01` em vez de `132,20`.

## Goals / Non-Goals

**Goals:**
- Corrigir a digitação tecla a tecla em todo campo monetário (`inpMoeda`), para qualquer tela que já usa ou venha a usar a máscara.
- Não alterar o comportamento já correto e testado da máscara de documento (CPF/CNPJ).
- Cobrir o cenário com teste automatizado que dispara múltiplos eventos `input` em sequência (não um valor atribuído de uma vez).

**Non-Goals:**
- Não é objetivo deste change permitir edição estável no meio de um valor monetário já preenchido (ex.: clicar entre os dígitos de `1.500,00` e inserir um dígito ali, esperando que o resto do valor não se reinterprete). Isso é inerente ao modelo "dígitos entram pela direita": qualquer edição reconstrói o número inteiro a partir da sequência de dígitos resultante. O fluxo esperado para corrigir um valor é selecionar tudo e redigitar, como em apps bancários.
- Não altera `mascararMoeda`/`formatarCentavos` (a lógica de formatação em si está correta — o bug é só no reposicionamento de cursor).

## Decisions

1. **Duas estratégias de cursor, uma função nova em vez de parâmetro.**
   Em vez de adicionar uma flag/parâmetro a `reaplicarMascara` para escolher o comportamento, criar uma segunda função em `ui/mascara.ts`, `reaplicarMascaraAoFim(campo, mascarar)`, dedicada ao caso "o cursor sempre vai para o fim depois de remascarar". `ui/moeda.ts` passa a chamar essa função; `ui/documento.ts` continua chamando `reaplicarMascara` sem mudanças.
   - Alternativa considerada: ajustar a contagem de `digitosAntes` em `reaplicarMascara` para ignorar zeros de preenchimento. Rejeitada porque `reaplicarMascara` não tem (e não deveria ter) conhecimento de que `formatarCentavos` insere padding — isso acoplaria uma função genérica de reposicionamento de cursor aos detalhes internos de uma máscara específica. Separar em duas funções, cada uma com a estratégia certa para o seu formato, é mais simples e explícito.

2. **"Fim do campo" = sempre `novo.length`, independente de onde o cursor estava antes de digitar.**
   Depois de qualquer tecla (inclusive apagar, colar, ou digitar com o cursor clicado no meio de um valor pré-existente), o cursor é reposicionado no fim do valor remascarado. Isso é consistente com o próprio modelo da máscara (todo o número é reconstruído a cada tecla a partir da sequência de dígitos) e com os cenários já documentados em `specs/mascara-monetaria` (digitar em campo vazio, apagar do final, colar) — nenhum cenário depende de edição estável no meio do valor.
   - Alternativa considerada: tentar preservar a posição "correta" mesmo com padding, contando só dígitos realmente digitados pelo usuário. Rejeitada por complexidade desproporcional ao ganho: exigiria rastrear histórico de digitação por campo, e ainda assim a reinterpretação completa do número a cada tecla tornaria a experiência de editar no meio confusa de qualquer forma (como qualquer app bancário com esse estilo de máscara).

## Riscos / Trade-offs

- **[Risco]** Usuário clica no meio de um valor já preenchido (editando um título existente) para corrigir um único dígito, digita, e o cursor pula para o fim em vez de continuar ali. → **Mitigação**: comportamento aceito e documentado (ver Non-Goals); é o mesmo modelo de apps bancários reais, onde o campo de valor normalmente nem permite edição posicional. Nenhum cenário da spec atual promete edição estável no meio.
- **[Risco]** Campo perde o foco entre o disparo do evento e a reaplicação da máscara (ex.: em testes ou automações). → **Mitigação**: `reaplicarMascaraAoFim` replica a guarda já existente em `reaplicarMascara` (`if (campo.ownerDocument.activeElement !== campo) return;` antes de mexer na seleção) — não houve mudança de risco aqui, só reaproveito do padrão.
- **[Risco]** Regressão na máscara de documento (CPF/CNPJ) por engano ao tocar em `ui/mascara.ts`. → **Mitigação**: `reaplicarMascara` (usada por `ui/documento.ts`) não é modificada, apenas uma nova função é adicionada ao lado; `ui/documento.test.ts` continua cobrindo o comportamento existente sem alteração.

## Plano de Migração

Mudança isolada ao frontend, sem dados ou contrato de API envolvidos. Deploy normal junto com o restante do frontend; rollback é reverter o commit/PR caso algo inesperado apareça. Nenhuma migração de dados ou flag necessária.

## Questões Abertas

Nenhuma.

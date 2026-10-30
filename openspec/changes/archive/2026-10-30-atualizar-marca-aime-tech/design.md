## Context

A marca iSolutis está espalhada em três camadas: ativos (`frontend/public/logo*.png`, cópia idêntica em `backend/app/documents/assets/`), código/UI (títulos, `alt`, textos, mensagens, e-mails, 2FA, API) e tema (`tokens.css`, `PALETA_PADRAO`, `login.css`). O kit AIME Tech (`AIME_Tech_Kit/`) traz logos em SVG/PNG por variante de cor, `favicon.ico`, ícones PNG e `AIME_Tech_app.svg`, e a paleta em `05_Web/cores.css`.

`identidade.ts` já deriva os tons dos temas a partir de `{primaria, destaque}` com contraste mínimo garantido, e cada empresa pode salvar paleta e logomarca próprias; o padrão só vale para quem não personalizou.

## Goals / Non-Goals

**Goals:**
- Toda referência de marca ao produto vira "AIME Tech Hub" / AIME Tech, com logos e favicon do kit.
- Paleta AIME como padrão nos temas claro e escuro, mantendo legibilidade (contraste de texto ≥ 4,5:1).
- Nenhuma alteração de banco, migrations ou contrato de API.

**Non-Goals:**
- Renomear repositório, pacotes, workflows ou fixtures de teste.
- Trocar fontes (o guia cita Inter como apoio; fica fora).
- Alterar o nome da empresa gravada no banco ou as paletas/logos personalizadas já salvas.

## Decisions

### 1. Logo por tipo de fundo
Telas pré-login e convite/onboarding têm fundo escuro (`.login`) → `horizontal_reverso` em **SVG** (nítido e leve). PDFs e e-mails de fundo claro → `horizontal_cor`; o PDF/WeasyPrint recebe PNG (data URL), então os assets do backend são PNG exportados do kit. O menu lateral (fundo da cor primária) usa `reverso`; o ícone recolhido (`marca-min`) usa o símbolo (`simbolo_reverso`/ícone). Alternativa descartada: `horizontal_branco` (perde as cores do símbolo).

Os `<img>` trocam `height` para a proporção ~3,5:1 (largura 200 → altura ~56) para evitar salto de layout.

### 2. Favicon
`public/favicon.ico`, `public/icon.svg` (de `AIME_Tech_app.svg`) e `public/apple-touch-icon.png` (180). Três `<link>` no `index.html`. O ícone tem fundo petróleo próprio, legível em abas claras e escuras. Os `logo.png`/`logo-horizontal.png` antigos são removidos do frontend por não terem mais uso; no backend são substituídos pelos novos com os mesmos nomes (referenciados por `render.py`).

### 3. Mapeamento de paleta
Mantém os **nomes** dos tokens existentes (`--navy`, `--teal`…) e troca só os valores, para não espalhar renomeação por toda a base de CSS; a dívida semântica (`--teal` guardando o índigo) é registrada e tratada em change próprio. Mapeamento: `--navy/--accent` → petróleo `#0B2D3B`; `--navy-deep` → petróleo mais escuro derivado; `--teal` / `--teal-mid` → índigo `#4F6B8F`; `--teal-pale` → lilás claro derivado de `#A7AFC7`; `--canvas/--sunk` → off-white `#F7F6F2`; `--bar-b` → lilás; login: fundo petróleo escuro e anel em lilás/champagne. `PALETA_PADRAO = { primaria: "#0B2D3B", destaque: "#4F6B8F" }`, nome "AIME Tech (padrão)".

No tema escuro, índigo sobre fundo petróleo tem contraste baixo para texto; o destaque no escuro usa o lilás `#A7AFC7` (verificar ≥ 4,5:1). Cores semânticas ok/warn/bad/info não mudam.

### 4. Nome do produto e textos
"AIME Tech Hub" em e-mails, 2FA, título da API e mensagens; `<title>` e título dinâmico da aba viram "AIME Tech Hub" (`${nome} · AIME Tech Hub`, onde `nome` continua vindo do cadastro). PDFs: `PADRAO = Identidade(nome="AIME Tech", subtitulo="Transformando o Futuro")` — só vale quando não há cadastro da empresa. CSV: `faturamento-aime-{ano}.csv`.

### 5. Sem tocar em dados
O nome "iSolutis" gravado na tabela `empresa` não é alterado; onde o nome vem do cadastro (parte do título da aba, cabeçalho/rodapé de PDFs com cadastro) a marca antiga continua até que seja editado na tela de Empresa. Migrations antigas (`0002`, `0005`) e fixtures permanecem.

## Risks / Trade-offs

- **Marca híbrida via dado**: o nome da empresa cadastrado ainda diz "iSolutis" → documentar no resumo; edição pela tela de Empresa fica por conta do usuário.
- **Contraste**: índigo/lilás precisam ser validados nos dois temas → conferir com as funções de contraste de `identidade.ts` e visualmente nas telas principais.
- **Nome dos tokens desalinhado da cor** → dívida técnica registrada, change futuro.
- **Cache de favicon**: navegadores guardam o favicon antigo; pode exigir recarga forçada.
- **Assinatura 2FA**: o novo emissor só aparece em novos cadastros; os existentes continuam com "iSolutis Hub" no app autenticador.

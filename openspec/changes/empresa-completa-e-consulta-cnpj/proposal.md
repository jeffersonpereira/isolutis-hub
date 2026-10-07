## Why

"Dados da empresa" guarda apenas o nome. Para documentos, relatórios e integrações fiscais a empresa precisa de cadastro completo (inscrição, razão social, endereço, contato, dados fiscais). Além disso, quem digita um CNPJ em qualquer tela hoje preenche tudo à mão; a BrasilAPI permite preencher automaticamente.

## What Changes

- Modelagem completa da empresa: tipo de inscrição (CNPJ ou CPF) e número, razão social, nome fantasia, inscrições estadual/municipal, CNAE, regime tributário, situação cadastral, data de abertura, e-mail, telefone e endereço (CEP, logradouro, número, complemento, bairro, município/UF).
- Nova tela "Dados da empresa" em página de formulário com seções, edição livre e somente para administradores.
- **Proxy no backend** `GET /cnpj/{cnpj}` para a BrasilAPI (autenticado, validação do dígito verificador, limite de taxa, timeout, cache curto, erros tratados). O navegador nunca chama a BrasilAPI diretamente (a CSP `connect-src 'self'` permanece).
- Em toda tela com CNPJ (Dados da empresa, parceiros e clientes): ao digitar um CNPJ válido, consulta pelo proxy e preenche os campos; o usuário pode editar tudo. CPF não consulta serviço externo.
- **Reordenação**: em todas essas telas, "Tipo de inscrição" e "Número de inscrição" passam a ser os primeiros campos; os demais seguem a ordem atual.

## Capabilities

### New Capabilities
- `cadastro-empresa`: dados cadastrais completos da empresa e regras de edição.
- `consulta-cnpj`: consulta de CNPJ via proxy do backend, preenchimento automático e ordem dos campos de inscrição.

### Modified Capabilities
<!-- nenhuma spec existente de parceiros/empresa; requisitos entram como novas capabilities -->

## Impact

- Banco: migração aditiva na tabela `empresa` (colunas anuláveis, índice único parcial do CNPJ); município via tabela `municipio` existente.
- Backend: `models/parceiro.py` (Empresa), router/schemas de empresas, novo serviço e router de CNPJ, cliente HTTP (httpx) com timeout, rate limit existente (`app/ratelimit.py`).
- Frontend: `features/empresa.ts`, `features/parceiros/campos.ts`, `features/clientes.ts`, util de CNPJ, `api/endpoints.ts`.
- Dependência da change `combobox-pesquisavel` (município) é desejável, não obrigatória. Relação com `multi-empresa-sessao`: o CNPJ não é chave de identidade nem libera criação de empresas por usuários.

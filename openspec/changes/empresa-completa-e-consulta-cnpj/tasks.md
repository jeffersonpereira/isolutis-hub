## 1. Banco (DBA)

- [ ] 1.1 Revisar o modelo proposto de colunas da `empresa` com o skill `database-design`
- [ ] 1.2 Migração Alembic aditiva + SQL + down: colunas anuláveis, check de `tipo_inscricao`, índice único parcial de inscrição
- [ ] 1.3 Atualizar o model `Empresa` e os schemas de leitura/atualização

## 2. Backend

- [ ] 2.1 Extrair/reusar validação de CPF/CNPJ para uso do cadastro da empresa
- [ ] 2.2 Endpoint de atualização completa da empresa (somente admin) com erros claros de inscrição inválida/duplicada
- [ ] 2.3 Serviço de consulta de CNPJ (URL fixa, httpx com timeout, DTO próprio, cache curto, mapeamento de erros)
- [ ] 2.4 Router `GET /cnpj/{cnpj}` autenticado com rate limit
- [ ] 2.5 Testes: DV inválido, 404, indisponível/timeout, não autenticado, limite, cache; empresa: duplicidade e autorização

## 3. Frontend

- [ ] 3.1 Utilitário de CNPJ (máscara, DV, normalização) e `api.cnpj.consultar`
- [ ] 3.2 Tela "Dados da empresa" em formulário de página com seções (Inscrição, Identificação, Contato, Endereço, Fiscal)
- [ ] 3.3 Preenchimento automático reutilizável (só campos vazios; estados buscando/erro)
- [ ] 3.4 Reordenar inscrição para o topo e integrar a consulta em parceiros e clientes (`parceiros/campos.ts`)
- [ ] 3.5 Município por UF/IBGE no preenchimento; usar combobox pesquisável se a change estiver pronta
- [ ] 3.6 Testes do front (máscara/DV, preenchimento, falha) e e2e do fluxo de empresa

## 4. Validação

- [ ] 4.1 Rodar migração up/down em base de teste, suítes de backend/front/e2e e revisar segurança do proxy e o diff

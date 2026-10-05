## Why

O sistema atual atende uma empresa e apenas parte dos registros carrega `company_id`; os serviços ainda selecionam a empresa mais antiga cadastrada. Isso impede isolamento confiável entre organizações e deixa dados comerciais sem proprietário explícito. A mudança prepara o Hub para múltiplas empresas, com a empresa como dona dos dados operacionais e fronteira de autorização.

## What Changes

- **BREAKING** Renomear o conceito e a tabela `companies` para `empresa`, e padronizar referências `company_id` como `empresa_id`.
- Atribuir os dados operacionais a uma empresa, incluindo comercial, financeiro, projetos e tarefas.
- Vincular usuários às empresas e validar o acesso e o papel do usuário em cada operação.
- Permitir classificações personalizadas de parceiros com múltiplas tags por parceiro e filtros por tags.
- Reforçar integridade referencial para impedir relações entre dados de empresas diferentes.
- Migrar os dados existentes para a empresa iSolutis sem perda de relações ou histórico.

## Capabilities

### New Capabilities
- `empresa-multi-tenancy`: propriedade dos dados, associação de usuários a empresas, tags personalizadas de parceiros e isolamento das operações por empresa.

### Modified Capabilities

## Impact

- PostgreSQL: schema, constraints, índices, migrações e carga inicial.
- Backend: autenticação/autorização, escopo de consultas, serviços e importador legado.
- Frontend e API: seleção de empresa ativa quando aplicável, contratos e operações por tenant.
- Documentação, OpenAPI, testes SQL, integração e E2E.

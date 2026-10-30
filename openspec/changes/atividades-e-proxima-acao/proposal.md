# Proposal

## Why

O Hub registra o resultado da venda (negócio, orçamento, projeto), mas não o relacionamento: ligações, reuniões e
combinados ficam fora do sistema, e o conhecimento do cliente se perde quando o vendedor muda. Também não há como saber
qual é o próximo passo de cada negócio aberto, então negócios esfriam sem que ninguém perceba. Esta é a maior lacuna
apontada na avaliação do produto como CRM e a que mais aumenta o uso diário pela equipe comercial.

## What Changes

- Nova **linha do tempo de atividades** por cliente: registros datados do tipo nota, ligação, reunião ou e-mail, com
  responsável e descrição, opcionalmente ligados a um negócio do mesmo cliente.
- A linha do tempo aparece no cliente (todas as atividades dele) e no negócio (só as atividades daquele negócio).
- Cada negócio aberto passa a ter uma **próxima ação** (o que fazer + data). **BREAKING**: criar, editar ou mover um
  negócio para uma etapa aberta sem próxima ação passa a ser recusado pela API. Negócios ganhos ou perdidos não têm
  próxima ação.
- **Concluir a próxima ação** registra uma atividade e define a ação seguinte numa única operação.
- Os cartões do funil mostram a próxima ação e destacam as que venceram.
- Dois novos alertas no painel (para quem tem permissão comercial): negócios abertos **sem próxima ação** e com
  **próxima ação vencida**.

## Capabilities

### New Capabilities
- `atividades-comerciais`: registro e consulta da linha do tempo de interações com clientes e negócios (tipos, autoria,
  vínculo cliente/negócio, edição e exclusão).
- `proxima-acao-negocio`: obrigatoriedade, ciclo de vida e conclusão da próxima ação de negócios abertos, e sua exibição
  no funil.

### Modified Capabilities
- `painel-alertas`: adiciona os alertas de negócios sem próxima ação e com próxima ação vencida.

## Impact

- **Banco**: nova tabela `atividades` (com auditoria, `empresa_id` e RLS como as demais) e colunas `proxima_acao` e
  `proxima_acao_em` em `negocios` (migração 0012, com script de volta).
- **API**: novas rotas `/atividades` (permissão `comercial`); `POST/PUT /negocios` e `PATCH /negocios/{id}/etapa`
  passam a exigir a próxima ação em etapas abertas; nova rota de conclusão da ação; `GET /painel` ganha dois alertas.
  Clientes externos da API que criam negócios precisam enviar os novos campos.
- **Frontend**: `features/clientes.ts`, `features/negocios.ts` e `features/painel.ts`; novo componente de linha do tempo.
- **Dados existentes**: negócios abertos já cadastrados ficam sem próxima ação até a próxima edição e aparecem no
  alerta "sem próxima ação", o que é o efeito desejado.

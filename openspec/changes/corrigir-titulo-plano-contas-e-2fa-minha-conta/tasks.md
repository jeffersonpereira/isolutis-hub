## 1. Diagnóstico (registrar a causa-raiz em cada item)

- [ ] 1.1 Reproduzir "sem contas" no lançamento de título (console, aba Rede, resposta de `GET /financeiro/plano-contas`) e anotar a causa
- [ ] 1.2 Consultar os dados da empresa afetada: contas analíticas por natureza e filhas com natureza divergente da raiz
- [ ] 1.3 Reproduzir a falha de ativação do 2FA em "Minha conta" (setup, confirmar, pós-token) e anotar a causa

## 2. Título financeiro

- [ ] 2.1 Corrigir a causa encontrada em 1.1/1.2 (código e/ou migração corretiva idempotente de natureza)
- [x] 2.2 Diferenciar estados carregando/vazio/erro no select de conta do plano
- [x] 2.3 Teste de backend: natureza herdada e validação de título × natureza (já cobertos por `test_plano_de_contas_hierarquia_e_heranca` e `test_titulo_so_em_conta_analitica_e_com_natureza_compativel`; execução depende do Postgres de testes)
- [ ] 2.4 Teste de front: opções por tipo, limpeza ao trocar tipo, estado de erro

## 3. 2FA em Minha conta

- [ ] 3.1 Corrigir a causa encontrada em 1.3
- [x] 3.2 Desabilitar "Ativar 2FA" com o fluxo aberto; mensagem de erro clara no setup
- [ ] 3.3 Teste de backend: setup → confirmar → token válido para a empresa ativa
- [ ] 3.4 Teste e2e: ativar 2FA e navegar sem novo login

## 4. Validação

- [ ] 4.1 Rodar suítes de backend, front e e2e afetadas e revisar o diff

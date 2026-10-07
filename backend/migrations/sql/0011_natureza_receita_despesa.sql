-- 0011 · plano_contas.natureza aceita somente 'R' (receita) e 'D' (despesa).
--
-- Alinha bancos que receberam, fora das migrações, a coluna como text com seis categorias
-- (RECEITAS, CUSTOS, DESPESAS, INVESTIMENTOS, MOVIMENTAÇÕES FINANCEIRAS, EMPRÉSTIMOS E FINANCIAMENTOS)
-- ao que o código, a API e o front esperam. É idempotente: em bancos criados pelas migrações (char(1) com R/D) não muda nada.
--
-- Conversão dos dados existentes: RECEITAS -> 'R'; qualquer outra categoria -> 'D'. As categorias "movimentações
-- financeiras" e "empréstimos e financiamentos" podiam ser entrada ou saída e não dá para decidir isso aqui:
-- revise-as depois da migração (ou recarregue o plano de contas).
--
-- O trigger do título volta à regra RN04: conta a pagar exige despesa; conta a receber exige receita.

ALTER TABLE plano_contas DROP CONSTRAINT IF EXISTS ck_plano_contas_natureza;

ALTER TABLE plano_contas
  ALTER COLUMN natureza TYPE char(1)
  USING (CASE WHEN natureza::text IN ('R', 'RECEITAS') THEN 'R' ELSE 'D' END);

ALTER TABLE plano_contas ADD CONSTRAINT ck_plano_contas_natureza CHECK (natureza IN ('R', 'D'));

CREATE OR REPLACE FUNCTION tg_titulo_financeiro_regras() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  v_conta plano_contas%ROWTYPE;
BEGIN
  SELECT * INTO v_conta FROM plano_contas WHERE id = NEW.plano_conta_id;
  IF NOT FOUND OR v_conta.tipo_conta <> 'A' THEN
    RAISE EXCEPTION 'títulos só podem ser lançados em conta analítica do plano de contas' USING ERRCODE = 'check_violation';
  END IF;
  IF (NEW.tipo_conta = 'P' AND v_conta.natureza <> 'D') OR (NEW.tipo_conta = 'R' AND v_conta.natureza <> 'R') THEN
    RAISE EXCEPTION 'conta a pagar exige conta de despesa; conta a receber exige conta de receita' USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END
$$;

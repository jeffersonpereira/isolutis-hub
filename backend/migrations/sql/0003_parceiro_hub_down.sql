-- A migração 0003 remove a tabela `clientes` depois de fundi-la em `parceiro_negocio`; não há reversão automática
-- (parceiros que não são clientes e papéis adicionais não cabem no modelo antigo). Para voltar: restaure o backup.
DO $$
BEGIN
  RAISE EXCEPTION 'A migração 0003 (parceiro como hub) é irreversível. Restaure o backup feito antes de aplicá-la.';
END
$$;

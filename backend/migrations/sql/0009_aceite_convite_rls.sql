-- Migração 0009: aceite de convite sob RLS.
--
-- O aceite é uma rota pública (sem empresa ativa) e quem aceita ainda não é administrador da empresa.
-- As políticas de usuario_empresa só permitem INSERT/UPDATE a administradores da empresa ativa, então a API
-- (papel hub_runtime, sem BYPASSRLS) não consegue criar nem reativar a membership por INSERT/UPDATE direto.
--
-- Esta função, no padrão de criar_empresa, é o único caminho: confere que o convite é do usuário informado,
-- está pendente e dentro do prazo e só então cria ou reativa a membership com o papel do convite e consome o
-- convite, tudo na mesma transação. Mesmo com um bug na API ela só cria membership que um convite válido autoriza.
CREATE FUNCTION vincular_membro_por_convite(p_convite_id integer, p_usuario_id uuid) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
DECLARE
  v_convite public.convites%ROWTYPE;
BEGIN
  -- Bloqueia o convite: aceites simultâneos do mesmo token são serializados.
  SELECT c.* INTO v_convite
  FROM public.convites c
  JOIN public.usuarios u ON u.email = c.email
  WHERE c.id = p_convite_id AND u.id = p_usuario_id AND u.ativo
  FOR UPDATE OF c;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'convite nao corresponde a um usuario ativo' USING ERRCODE = 'insufficient_privilege';
  END IF;
  IF v_convite.usado_em IS NOT NULL OR v_convite.expira_em < now() THEN
    RAISE EXCEPTION 'convite ja utilizado ou expirado' USING ERRCODE = 'check_violation';
  END IF;

  INSERT INTO public.usuario_empresa (empresa_id, usuario_id, papel, ativo)
  VALUES (v_convite.empresa_id, p_usuario_id, v_convite.papel, true)
  ON CONFLICT (empresa_id, usuario_id) DO UPDATE SET papel = EXCLUDED.papel, ativo = true;

  UPDATE public.convites SET usado_em = now() WHERE id = v_convite.id;
END
$$;
REVOKE ALL ON FUNCTION vincular_membro_por_convite(integer, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION vincular_membro_por_convite(integer, uuid) TO hub_runtime;

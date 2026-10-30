-- 0018 · Adicionar membro já cadastrado direto, sem convite por e-mail.
--
-- Quando o e-mail informado já é de uma conta ativa, não há por que esperar o aceite de um convite: a pessoa já tem
-- senha própria, então a membership entra ativa na hora e a empresa passa a aparecer para ela escolher no próximo
-- login. Só quando o e-mail ainda não tem conta é que continuamos pelo convite — é a única forma de a pessoa definir
-- uma senha.

DROP FUNCTION IF EXISTS plataforma_convidar(uuid, text, text);

CREATE FUNCTION plataforma_convidar(p_empresa uuid, p_email text, p_papel text)
RETURNS TABLE (convite_id integer, token uuid, usuario_id uuid)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
DECLARE
  v_operador uuid := public.plataforma_operador_atual();
  v_email text := lower(btrim(coalesce(p_email, '')));
  v_usuario uuid;
  v_convite integer;
  v_token uuid;
BEGIN
  IF p_papel NOT IN ('admin', 'financeiro', 'comercial', 'membro') THEN
    RAISE EXCEPTION 'Papel inválido.' USING ERRCODE = 'check_violation';
  END IF;
  IF v_email !~ '^[^@[:space:]]+@[^@[:space:]]+$' THEN
    RAISE EXCEPTION 'Informe um e-mail válido.' USING ERRCODE = 'check_violation';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.empresa WHERE id = p_empresa) THEN
    RAISE EXCEPTION 'Empresa não encontrada.' USING ERRCODE = 'no_data_found';
  END IF;
  IF EXISTS (
    SELECT 1 FROM public.usuario_empresa ue JOIN public.usuarios u ON u.id = ue.usuario_id
    WHERE ue.empresa_id = p_empresa AND ue.ativo AND u.ativo AND u.email = v_email
  ) THEN
    RAISE EXCEPTION 'Este e-mail já é membro da empresa.' USING ERRCODE = 'check_violation';
  END IF;

  SELECT id INTO v_usuario FROM public.usuarios WHERE email = v_email AND ativo;
  IF v_usuario IS NOT NULL THEN
    INSERT INTO public.usuario_empresa (empresa_id, usuario_id, papel, ativo)
    VALUES (p_empresa, v_usuario, p_papel, true)
    ON CONFLICT ON CONSTRAINT pk_usuario_empresa DO UPDATE SET papel = excluded.papel, ativo = true;

    INSERT INTO public.auditoria_plataforma (operador_id, empresa_id, acao, depois)
    VALUES (v_operador, p_empresa, 'membro_adicionado', jsonb_build_object('email', v_email, 'papel', p_papel));

    RETURN QUERY SELECT NULL::integer, NULL::uuid, v_usuario;
    RETURN;
  END IF;

  DELETE FROM public.convites
  WHERE empresa_id = p_empresa AND email = v_email AND usado_em IS NULL AND expira_em > now();
  INSERT INTO public.convites (email, empresa_id, papel, criado_por, expira_em)
  VALUES (v_email, p_empresa, p_papel, v_operador, now() + interval '72 hours')
  RETURNING id, convites.token INTO v_convite, v_token;

  INSERT INTO public.auditoria_plataforma (operador_id, empresa_id, acao, depois)
  VALUES (v_operador, p_empresa, 'membro_convidado', jsonb_build_object('email', v_email, 'papel', p_papel));

  RETURN QUERY SELECT v_convite, v_token, NULL::uuid;
END
$$;
REVOKE ALL ON FUNCTION plataforma_convidar(uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_convidar(uuid, text, text) TO hub_plataforma;

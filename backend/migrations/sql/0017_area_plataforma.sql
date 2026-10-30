-- 0017 · Área da plataforma: operador, status da empresa, auditoria e funções de provisionamento.
--
-- O operador (a AIME Tech) cria empresas e gerencia membros sem enxergar dados de negócio. As rotas /plataforma usam o
-- papel hub_plataforma, que NÃO tem privilégio em nenhuma tabela: só executa as funções plataforma_* abaixo
-- (SECURITY DEFINER, padrão de vincular_membro_por_convite). Cada função confere que app_usuario_id() é operador e grava
-- a auditoria na mesma transação.
--
-- hub_plataforma é criado aqui sem login quando não existe. Para ligar a credencial:
--   ALTER ROLE hub_plataforma LOGIN PASSWORD '...';

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hub_plataforma') THEN
    CREATE ROLE hub_plataforma NOLOGIN;
  END IF;
END $$;

-- 1. Operadores --------------------------------------------------------------------------------------------------
CREATE TABLE operador_plataforma (
  usuario_id uuid PRIMARY KEY REFERENCES usuarios (id),
  criado_em  timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON operador_plataforma FROM PUBLIC, hub_runtime, hub_plataforma;

-- 2. Status da empresa -------------------------------------------------------------------------------------------
ALTER TABLE empresa ADD COLUMN status varchar(10) NOT NULL DEFAULT 'ativa';
ALTER TABLE empresa ADD CONSTRAINT ck_empresa_status CHECK (status IN ('ativa', 'suspensa'));

-- O admin da empresa pode atualizar a própria empresa (política empresa_admin_atualiza), mas não o status: só as
-- funções do operador (executadas pelo dono, não por hub_runtime) mudam essa coluna.
CREATE FUNCTION tg_empresa_status_so_plataforma() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status IS DISTINCT FROM OLD.status AND current_user IN ('hub_runtime', 'hub_plataforma') THEN
    RAISE EXCEPTION 'o status da empresa so e alterado pela area da plataforma' USING ERRCODE = 'insufficient_privilege';
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER empresa_status_so_plataforma BEFORE UPDATE ON empresa
  FOR EACH ROW EXECUTE FUNCTION tg_empresa_status_so_plataforma();

-- 3. Auditoria (somente inserção) --------------------------------------------------------------------------------
CREATE TABLE auditoria_plataforma (
  id          bigserial PRIMARY KEY,
  operador_id uuid NOT NULL REFERENCES usuarios (id),
  empresa_id  uuid REFERENCES empresa (id),
  acao        varchar(40) NOT NULL,
  antes       jsonb,
  depois      jsonb,
  criado_em   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_auditoria_plataforma_empresa ON auditoria_plataforma (empresa_id, criado_em DESC);
REVOKE ALL ON auditoria_plataforma FROM PUBLIC, hub_runtime, hub_plataforma;
REVOKE ALL ON SEQUENCE auditoria_plataforma_id_seq FROM PUBLIC, hub_runtime, hub_plataforma;

CREATE FUNCTION tg_auditoria_plataforma_imutavel() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'a auditoria da plataforma nao pode ser alterada' USING ERRCODE = 'insufficient_privilege';
END
$$;
CREATE TRIGGER auditoria_plataforma_imutavel BEFORE UPDATE OR DELETE ON auditoria_plataforma
  FOR EACH ROW EXECUTE FUNCTION tg_auditoria_plataforma_imutavel();

-- 4. Funções -----------------------------------------------------------------------------------------------------
-- A aplicação deixa de criar empresas: criar_empresa (0005) sai do hub_runtime.
REVOKE EXECUTE ON FUNCTION criar_empresa(text) FROM hub_runtime;

-- Quem está logado é operador? (a API pergunta com hub_runtime para decidir o acesso e o menu)
CREATE FUNCTION eh_operador_plataforma() RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
  SELECT EXISTS (SELECT 1 FROM public.operador_plataforma WHERE usuario_id = public.app_usuario_id())
$$;
REVOKE ALL ON FUNCTION eh_operador_plataforma() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION eh_operador_plataforma() TO hub_runtime, hub_plataforma;

-- Uso interno das demais: devolve o operador ou recusa.
CREATE FUNCTION plataforma_operador_atual() RETURNS uuid
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
DECLARE
  v_usuario uuid := public.app_usuario_id();
BEGIN
  IF v_usuario IS NULL OR NOT EXISTS (SELECT 1 FROM public.operador_plataforma WHERE usuario_id = v_usuario) THEN
    RAISE EXCEPTION 'acesso restrito ao operador da plataforma' USING ERRCODE = 'insufficient_privilege';
  END IF;
  RETURN v_usuario;
END
$$;
REVOKE ALL ON FUNCTION plataforma_operador_atual() FROM PUBLIC;

CREATE FUNCTION plataforma_listar_empresas(p_busca text DEFAULT NULL, p_empresa uuid DEFAULT NULL)
RETURNS TABLE (id uuid, nome text, inscricao text, status text, membros_ativos bigint, criado_em timestamptz)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
BEGIN
  PERFORM public.plataforma_operador_atual();
  RETURN QUERY
  SELECT e.id, e.nome::text, e.inscricao::text, e.status::text,
         (SELECT count(*) FROM public.usuario_empresa ue
           JOIN public.usuarios u ON u.id = ue.usuario_id
          WHERE ue.empresa_id = e.id AND ue.ativo AND u.ativo),
         e.created_at
  FROM public.empresa e
  WHERE (p_empresa IS NULL OR e.id = p_empresa)
    AND (p_busca IS NULL OR btrim(p_busca) = ''
         OR position(lower(btrim(p_busca)) IN lower(e.nome)) > 0
         OR position(regexp_replace(p_busca, '\D', '', 'g') IN coalesce(e.inscricao, '')) > 0
            AND regexp_replace(p_busca, '\D', '', 'g') <> '')
  ORDER BY e.nome;
END
$$;
REVOKE ALL ON FUNCTION plataforma_listar_empresas(text, uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_listar_empresas(text, uuid) TO hub_plataforma;

CREATE FUNCTION plataforma_criar_empresa(p_nome text, p_inscricao text, p_email text)
RETURNS TABLE (empresa_id uuid, convite_id integer, token uuid)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
DECLARE
  v_operador uuid := public.plataforma_operador_atual();
  v_nome text := btrim(coalesce(p_nome, ''));
  v_email text := lower(btrim(coalesce(p_email, '')));
  v_inscricao text := nullif(regexp_replace(coalesce(p_inscricao, ''), '\D', '', 'g'), '');
  v_empresa uuid;
  v_convite integer;
  v_token uuid;
BEGIN
  IF v_nome = '' OR char_length(v_nome) > 150 THEN
    RAISE EXCEPTION 'Informe o nome da empresa (até 150 caracteres).' USING ERRCODE = 'check_violation';
  END IF;
  IF v_email !~ '^[^@[:space:]]+@[^@[:space:]]+$' THEN
    RAISE EXCEPTION 'Informe um e-mail válido para o administrador.' USING ERRCODE = 'check_violation';
  END IF;
  IF v_inscricao IS NOT NULL AND v_inscricao !~ '^[0-9]{14}$' THEN
    RAISE EXCEPTION 'O CNPJ precisa ter 14 dígitos.' USING ERRCODE = 'check_violation';
  END IF;
  IF v_inscricao IS NOT NULL AND EXISTS (
    SELECT 1 FROM public.empresa WHERE tipo_inscricao = 'CNPJ' AND inscricao = v_inscricao
  ) THEN
    RAISE EXCEPTION 'Já existe uma empresa com este CNPJ.' USING ERRCODE = 'check_violation';
  END IF;

  INSERT INTO public.empresa (nome, tipo_inscricao, inscricao)
  VALUES (v_nome, CASE WHEN v_inscricao IS NULL THEN NULL ELSE 'CNPJ' END, v_inscricao)
  RETURNING id INTO v_empresa;

  INSERT INTO public.convites (email, empresa_id, papel, criado_por, expira_em)
  VALUES (v_email, v_empresa, 'admin', v_operador, now() + interval '72 hours')
  RETURNING id, convites.token INTO v_convite, v_token;

  INSERT INTO public.auditoria_plataforma (operador_id, empresa_id, acao, depois)
  VALUES (v_operador, v_empresa, 'empresa_criada',
          jsonb_build_object('nome', v_nome, 'inscricao', v_inscricao, 'admin_inicial', v_email));

  RETURN QUERY SELECT v_empresa, v_convite, v_token;
END
$$;
REVOKE ALL ON FUNCTION plataforma_criar_empresa(text, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_criar_empresa(text, text, text) TO hub_plataforma;

CREATE FUNCTION plataforma_definir_status(p_empresa uuid, p_status text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
DECLARE
  v_operador uuid := public.plataforma_operador_atual();
  v_antes text;
BEGIN
  IF p_status NOT IN ('ativa', 'suspensa') THEN
    RAISE EXCEPTION 'Status inválido.' USING ERRCODE = 'check_violation';
  END IF;
  SELECT status INTO v_antes FROM public.empresa WHERE id = p_empresa FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Empresa não encontrada.' USING ERRCODE = 'no_data_found';
  END IF;
  IF v_antes = p_status THEN
    RETURN;
  END IF;
  UPDATE public.empresa SET status = p_status, updated_at = now() WHERE id = p_empresa;
  INSERT INTO public.auditoria_plataforma (operador_id, empresa_id, acao, antes, depois)
  VALUES (v_operador, p_empresa, CASE WHEN p_status = 'suspensa' THEN 'empresa_suspensa' ELSE 'empresa_reativada' END,
          jsonb_build_object('status', v_antes), jsonb_build_object('status', p_status));
END
$$;
REVOKE ALL ON FUNCTION plataforma_definir_status(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_definir_status(uuid, text) TO hub_plataforma;

CREATE FUNCTION plataforma_listar_membros(p_empresa uuid)
RETURNS TABLE (usuario_id uuid, nome text, email text, papel text, ativo boolean, usuario_ativo boolean,
               ultimo_acesso timestamptz)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
BEGIN
  PERFORM public.plataforma_operador_atual();
  RETURN QUERY
  SELECT u.id, u.nome::text, u.email::text, ue.papel::text, ue.ativo, u.ativo, u.ultimo_acesso
  FROM public.usuario_empresa ue
  JOIN public.usuarios u ON u.id = ue.usuario_id
  WHERE ue.empresa_id = p_empresa
  ORDER BY ue.ativo DESC, u.nome;
END
$$;
REVOKE ALL ON FUNCTION plataforma_listar_membros(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_listar_membros(uuid) TO hub_plataforma;

CREATE FUNCTION plataforma_listar_convites(p_empresa uuid)
RETURNS TABLE (id integer, email text, papel text, criado_em timestamptz, expira_em timestamptz)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
BEGIN
  PERFORM public.plataforma_operador_atual();
  RETURN QUERY
  SELECT c.id, c.email::text, c.papel::text, c.criado_em, c.expira_em
  FROM public.convites c
  WHERE c.empresa_id = p_empresa AND c.usado_em IS NULL AND c.expira_em > now()
  ORDER BY c.criado_em DESC;
END
$$;
REVOKE ALL ON FUNCTION plataforma_listar_convites(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_listar_convites(uuid) TO hub_plataforma;

-- Convida (ou reenvia: o convite pendente anterior do mesmo e-mail é substituído).
CREATE FUNCTION plataforma_convidar(p_empresa uuid, p_email text, p_papel text)
RETURNS TABLE (convite_id integer, token uuid)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
DECLARE
  v_operador uuid := public.plataforma_operador_atual();
  v_email text := lower(btrim(coalesce(p_email, '')));
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

  DELETE FROM public.convites
  WHERE empresa_id = p_empresa AND email = v_email AND usado_em IS NULL AND expira_em > now();
  INSERT INTO public.convites (email, empresa_id, papel, criado_por, expira_em)
  VALUES (v_email, p_empresa, p_papel, v_operador, now() + interval '72 hours')
  RETURNING id, convites.token INTO v_convite, v_token;

  INSERT INTO public.auditoria_plataforma (operador_id, empresa_id, acao, depois)
  VALUES (v_operador, p_empresa, 'membro_convidado', jsonb_build_object('email', v_email, 'papel', p_papel));

  RETURN QUERY SELECT v_convite, v_token;
END
$$;
REVOKE ALL ON FUNCTION plataforma_convidar(uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_convidar(uuid, text, text) TO hub_plataforma;

CREATE FUNCTION plataforma_cancelar_convite(p_empresa uuid, p_convite integer) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
DECLARE
  v_operador uuid := public.plataforma_operador_atual();
  v_email text;
BEGIN
  DELETE FROM public.convites WHERE id = p_convite AND empresa_id = p_empresa AND usado_em IS NULL
  RETURNING email INTO v_email;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Convite não encontrado.' USING ERRCODE = 'no_data_found';
  END IF;
  INSERT INTO public.auditoria_plataforma (operador_id, empresa_id, acao, antes)
  VALUES (v_operador, p_empresa, 'convite_cancelado', jsonb_build_object('email', v_email));
END
$$;
REVOKE ALL ON FUNCTION plataforma_cancelar_convite(uuid, integer) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_cancelar_convite(uuid, integer) TO hub_plataforma;

-- Troca o papel e/ou o estado de um membro; recusa deixar a empresa sem administrador ativo.
CREATE FUNCTION plataforma_definir_membro(p_empresa uuid, p_usuario uuid, p_papel text, p_ativo boolean) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public
SET row_security = off
AS $$
DECLARE
  v_operador uuid := public.plataforma_operador_atual();
  v_antes public.usuario_empresa%ROWTYPE;
BEGIN
  IF p_papel NOT IN ('admin', 'financeiro', 'comercial', 'membro') THEN
    RAISE EXCEPTION 'Papel inválido.' USING ERRCODE = 'check_violation';
  END IF;
  SELECT * INTO v_antes FROM public.usuario_empresa WHERE empresa_id = p_empresa AND usuario_id = p_usuario FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Membro não encontrado.' USING ERRCODE = 'no_data_found';
  END IF;
  IF v_antes.ativo AND v_antes.papel = 'admin' AND (p_papel <> 'admin' OR NOT p_ativo) AND NOT EXISTS (
    SELECT 1 FROM public.usuario_empresa ue JOIN public.usuarios u ON u.id = ue.usuario_id
    WHERE ue.empresa_id = p_empresa AND ue.usuario_id <> p_usuario AND ue.ativo AND u.ativo AND ue.papel = 'admin'
  ) THEN
    RAISE EXCEPTION 'Precisa existir pelo menos um administrador ativo na empresa.' USING ERRCODE = 'check_violation';
  END IF;
  IF v_antes.papel = p_papel AND v_antes.ativo = p_ativo THEN
    RETURN;
  END IF;
  UPDATE public.usuario_empresa SET papel = p_papel, ativo = p_ativo WHERE empresa_id = p_empresa AND usuario_id = p_usuario;
  INSERT INTO public.auditoria_plataforma (operador_id, empresa_id, acao, antes, depois)
  VALUES (v_operador, p_empresa, 'membro_alterado',
          jsonb_build_object('usuario_id', p_usuario, 'papel', v_antes.papel, 'ativo', v_antes.ativo),
          jsonb_build_object('usuario_id', p_usuario, 'papel', p_papel, 'ativo', p_ativo));
END
$$;
REVOKE ALL ON FUNCTION plataforma_definir_membro(uuid, uuid, text, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION plataforma_definir_membro(uuid, uuid, text, boolean) TO hub_plataforma;

-- hub_plataforma precisa só deste gancho do contexto da requisição (a sessão o chama a cada transação).
GRANT USAGE ON SCHEMA public TO hub_plataforma;
GRANT EXECUTE ON FUNCTION app_iniciar_contexto(uuid, uuid, boolean) TO hub_plataforma;

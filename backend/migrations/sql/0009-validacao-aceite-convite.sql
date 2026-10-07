-- Validação da migração 0009 (aceite de convite sob RLS). Rodar com a credencial MIGRADORA, DEPOIS de aplicar a 0009.
--
-- Parte 1: consultas de leitura (estado do banco). Parte 2: um bloco que exercita a função como o papel da API
-- (hub_runtime). O bloco termina com uma exceção proposital para desfazer tudo: NADA É GRAVADO. O resultado
-- aparece na mensagem de erro "VERIFICACAO (nada foi gravado)".
--
-- Se a Parte 2 falhar com "permission denied to set role", a credencial migradora não pode assumir hub_runtime;
-- nesse caso rode a Parte 2 como superusuário, ou execute uma vez: GRANT hub_runtime TO CURRENT_USER;

-- ===== Parte 1: estado =====
SELECT version_num AS revisao_alembic FROM alembic_version;

SELECT p.proname,
       p.prosecdef AS security_definer,
       p.proconfig AS configuracao_fixa,
       has_function_privilege('hub_runtime', p.oid, 'EXECUTE') AS runtime_executa,
       has_function_privilege('public', p.oid, 'EXECUTE')      AS public_executa
FROM pg_proc p
WHERE p.proname = 'vincular_membro_por_convite';
-- esperado: security_definer = true; configuracao_fixa com search_path e row_security=off;
--           runtime_executa = true; public_executa = false

SELECT rolname, rolsuper, rolbypassrls
FROM pg_roles
WHERE rolname IN ('hub_runtime', current_user)
ORDER BY rolname;
-- esperado: hub_runtime com rolsuper = false e rolbypassrls = false (senão a RLS não vale para a API)

-- ===== Parte 2: comportamento (desfeito ao final) =====
DO $$
DECLARE
  v_criador uuid := gen_random_uuid();
  v_alvo    uuid := gen_random_uuid();
  v_empresa uuid;
  v_convite integer;
  v_outro   integer;
  v_papel   text;
  v_usado   timestamptz;
  v_msgs    text := '';
BEGIN
  INSERT INTO usuarios (id, email, nome, senha_hash) VALUES
    (v_criador, 'criador.' || v_criador || '@verificacao.invalid', 'Criador', 'x'),
    (v_alvo,    'alvo.'    || v_alvo    || '@verificacao.invalid', 'Alvo', 'x');

  -- empresa pelo caminho oficial (SECURITY DEFINER), já que empresa não tem política de INSERT
  PERFORM set_config('app.usuario_id', v_criador::text, true);
  v_empresa := criar_empresa('__verificacao_convite__');
  PERFORM set_config('app.empresa_id', v_empresa::text, true);

  INSERT INTO convites (email, empresa_id, papel, criado_por, expira_em)
  SELECT email, v_empresa, 'membro', v_criador, now() + interval '1 hour' FROM usuarios WHERE id = v_alvo
  RETURNING id INTO v_convite;

  -- convite de OUTRO e-mail (o do criador), para testar o uso com o usuário errado
  INSERT INTO convites (email, empresa_id, papel, criado_por, expira_em)
  SELECT email, v_empresa, 'membro', v_criador, now() + interval '1 hour' FROM usuarios WHERE id = v_criador
  RETURNING id INTO v_outro;

  SET LOCAL ROLE hub_runtime;
  PERFORM set_config('app.usuario_id', '', true);
  PERFORM set_config('app.empresa_id', '', true);

  -- 1) INSERT direto como a API, sem empresa ativa e sem ser administrador: a RLS tem de recusar
  BEGIN
    INSERT INTO usuario_empresa (empresa_id, usuario_id, papel) VALUES (v_empresa, v_alvo, 'membro');
    v_msgs := v_msgs || E'\n[FALHA] INSERT direto em usuario_empresa foi aceito: a RLS nao esta protegendo a tabela';
  EXCEPTION WHEN insufficient_privilege THEN
    v_msgs := v_msgs || E'\n[OK]    INSERT direto recusado pela RLS (esperado)';
  END;

  -- 2) pela funcao, com o convite certo, a membership e criada e o convite consumido
  PERFORM vincular_membro_por_convite(v_convite, v_alvo);

  RESET ROLE;
  PERFORM set_config('app.empresa_id', v_empresa::text, true);
  SELECT papel INTO v_papel FROM usuario_empresa WHERE empresa_id = v_empresa AND usuario_id = v_alvo AND ativo;
  SELECT usado_em INTO v_usado FROM convites WHERE id = v_convite;
  IF v_papel = 'membro' AND v_usado IS NOT NULL THEN
    v_msgs := v_msgs || E'\n[OK]    funcao criou a membership com o papel do convite e consumiu o convite';
  ELSE
    v_msgs := v_msgs || E'\n[FALHA] funcao nao criou a membership ou nao consumiu o convite';
  END IF;

  SET LOCAL ROLE hub_runtime;

  -- 3) reuso do mesmo convite tem de ser recusado
  BEGIN
    PERFORM vincular_membro_por_convite(v_convite, v_alvo);
    v_msgs := v_msgs || E'\n[FALHA] convite ja usado foi aceito de novo';
  EXCEPTION WHEN check_violation THEN
    v_msgs := v_msgs || E'\n[OK]    convite ja usado recusado (esperado)';
  END;

  -- 4) convite de outro e-mail nao vale para este usuario
  BEGIN
    PERFORM vincular_membro_por_convite(v_outro, v_alvo);
    v_msgs := v_msgs || E'\n[FALHA] convite de outro e-mail foi aceito para o usuario errado';
  EXCEPTION WHEN insufficient_privilege THEN
    v_msgs := v_msgs || E'\n[OK]    convite de outro e-mail recusado (esperado)';
  END;

  RESET ROLE;
  RAISE EXCEPTION 'VERIFICACAO (nada foi gravado):%', v_msgs;
END
$$;

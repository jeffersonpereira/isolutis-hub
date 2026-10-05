# Auditoria de Segurança - RLS (Row Level Security)

**Status:** ⚠️ CRÍTICO - Requer verificação manual

## Visão Geral

O Supabase implementa Row Level Security (RLS) através de políticas SQL. Cada política controla quem pode ver/editar/deletar registros específicos. Este documento detalha as políticas críticas que devem ser verificadas.

## Políticas Críticas de RLS

### 1. Isolamento de Empresas

**Política:** `hub_eh_membro(user_id, empresa_id) -> boolean`

```sql
-- Verifica se usuário é membro ativo da empresa
CREATE OR REPLACE FUNCTION hub_eh_membro(p_usuario_id UUID, p_empresa_id UUID)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM usuario_empresa
    WHERE usuario_id = p_usuario_id
      AND empresa_id = p_empresa_id
      AND ativo = TRUE
  );
$$ LANGUAGE SQL;
```

**Testes Críticos:**
- [ ] Usuário A da Empresa X NÃO consegue listar clientes da Empresa Y
- [ ] Usuário A NÃO consegue acessar `/equipe` de Empresa Y
- [ ] Usuário A com `ativo=FALSE` NÃO consegue mais acessar dados

**Verificar:**
```sql
-- Teste: Usuário desativado pode ainda ver dados?
SELECT * FROM usuario_empresa WHERE usuario_id = 'uuid-teste' AND ativo = FALSE;
-- Se retornar registros, RLS pode estar falhando

-- Teste: Cross-empresa access
SET app.current_user_id = 'uuid-usuario-a';  -- Simular login
SET app.current_empresa_id = 'uuid-empresa-x';
SELECT COUNT(*) FROM cliente;  -- Deve retornar apenas clientes de Empresa X
SET app.current_empresa_id = 'uuid-empresa-y';
SELECT COUNT(*) FROM cliente;  -- Deve retornar 0 ou erro
```

---

### 2. Isolamento de Papéis (Admin vs Membro)

**Política:** Apenas `admin=true` pode gerenciar usuários

```sql
-- RLS Policy em usuario_empresa table
CREATE POLICY admin_only_usuarios ON usuario_empresa
  FOR ALL
  USING (
    hub_eh_membro(auth.uid(), empresa_id)
    AND hub_eh_admin(auth.uid(), empresa_id)
  );
```

**Testes Críticos:**
- [ ] Membro comum NÃO consegue atualizar outro membro
- [ ] Membro comum NÃO consegue deletar outro membro
- [ ] Membro comum NÃO consegue fazer alguém admin
- [ ] Admin consegue fazer tudo

**Verificar:**
```python
# No backend, ao chamar PATCH /usuarios/{id_}
usuario_atual = get_current_user()  # Membro comum
if not usuario_atual.admin:
    raise PermissionError("Apenas admins podem gerenciar usuários")
```

---

### 3. Proteção de Deletação (Soft Delete)

**Política:** Usuários deletados devem ter `ativo=FALSE`, não ser removidos

```sql
-- RLS Policy: Usuários inativos não aparecem em consultas normais
CREATE POLICY usuarios_ativos ON usuario_empresa
  FOR SELECT
  USING (ativo = TRUE);
```

**Testes Críticos:**
- [ ] Deletar usuário seta `ativo=FALSE`, não remove da DB
- [ ] Usuário deletado desaparece do frontend
- [ ] Reativar usuário reverte o acesso

---

### 4. Validação de Contexto Multi-Tenant

**Risco:** Backend não validar `empresa_id` do usuário

```python
# ❌ INSEGURO
@router.put("/usuarios/{id_}")
async def atualizar_usuario(
    id_: UUID,
    dados: UsuarioAtualizar,
    empresa: EmpresaAtual,  # Confia que vem correto
    sessao: Sessao,
):
    # Sem validar que `id_` pertence a `empresa`
    usuario = await sessao.get(Usuario, id_)
    usuario.nome = dados.nome
    await sessao.commit()

# ✅ SEGURO
async def atualizar_usuario(
    id_: UUID,
    dados: UsuarioAtualizar,
    empresa: EmpresaAtual,
    sessao: Sessao,
):
    # Validar que usuário pertence à empresa
    usuario = await sessao.scalar(
        select(Usuario)
        .where(
            Usuario.id == id_,
            Usuario.empresa_id == empresa.id,
        )
    )
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    usuario.nome = dados.nome
    await sessao.commit()
```

**Teste Manual:**
```bash
# Como Admin da Empresa A, tente atualizar usuário da Empresa B
curl -X PUT \
  https://api.hub/usuarios/uuid-usuario-empresa-b \
  -H "Authorization: Bearer token-admin-empresa-a" \
  -H "X-Empresa-ID: uuid-empresa-b" \
  -d '{"nome": "Hacked"}'

# Esperado: 404 ou 403 (acesso negado)
# Risco: Se retornar 200, há falha de isolamento
```

---

## Checklist de Auditoria

### Antes de Produção

- [ ] RLS está **habilitado** em todas as tabelas
- [ ] Política `hub_eh_membro` está compilada e funcional
- [ ] Teste de isolamento cross-empresa passou
- [ ] Teste de isolamento admin-membro passou
- [ ] Deletions usam soft-delete (ativo=FALSE)
- [ ] Backend valida `empresa_id` em todas as operações
- [ ] Session tokens não são expostos em logs
- [ ] Senhas são hasheadas com Argon2 (backend)
- [ ] JWT tokens têm expiração apropriada (< 1 hora)

### Testes Periódicos (após mudanças)

1. **Isolamento de Empresa**
   ```bash
   # Executar com usuário A e usuário B de empresas diferentes
   # Verificar que dados não vazam entre empresas
   ```

2. **Isolamento de Papel**
   ```bash
   # Executar com admin e membro
   # Verificar que membro não consegue escalar privilégios
   ```

3. **Proteção de Dados Sensíveis**
   ```bash
   # Procurar por senhas em logs
   # Procurar por tokens em responses
   grep -r "senha\|token\|password" logs/ | grep -v "hashed"
   ```

---

## Implementação Recomendada

### Backend (Python/FastAPI)

```python
from app.models import Usuario, UsuarioEmpresa
from sqlalchemy.orm import with_entities

async def validar_acesso_usuario(
    sessao: Sessao,
    usuario_requerente: Usuario,
    usuario_id: UUID,
    empresa_id: UUID,
) -> Usuario:
    """
    Validar que usuário requerente pode acessar outro usuário.
    Regras:
    - Apenas admins podem acessar usuários de sua empresa
    - Um usuário só consegue acessar a si mesmo
    """
    
    # Se tentando acessar si mesmo, permitir
    if usuario_requerente.id == usuario_id:
        usuario = await sessao.get(Usuario, usuario_id)
        if usuario and usuario.empresa_id == empresa_id:
            return usuario
    
    # Se não é admin, bloquear
    if not usuario_requerente.admin:
        raise HTTPException(
            status_code=403,
            detail="Apenas admins podem gerenciar usuários"
        )
    
    # Admin da empresa pode acessar usuários de sua empresa
    usuario = await sessao.scalar(
        select(Usuario).where(
            Usuario.id == usuario_id,
            Usuario.empresa_id == empresa_id,
        )
    )
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    return usuario
```

### Frontend (TypeScript)

```typescript
// Sempre enviar empresa_id explícito
const atualizar = async (usuarioId: string, dados: UsuarioAtualizar) => {
  const response = await http.put(
    `/usuarios/${usuarioId}`,
    dados,
    {
      headers: {
        "X-Empresa-ID": eu.empresa_id,  // Validação extra
      },
    }
  );
  return response;
};
```

---

## Referências

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [OWASP - Broken Access Control](https://owasp.org/www-project-top-ten/2021/A01_2021-broken_access_control/)
- [Testing RLS Policies](https://supabase.com/docs/guides/database/testing)

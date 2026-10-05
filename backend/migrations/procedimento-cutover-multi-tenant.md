# Procedimento de Cutover Multi-Tenant: Migração e Rollback

**Objetivo:** Ativar isolamento de tenant (RLS, FKs compostas, validações) em produção com segurança.

**Duração estimada:** 2-4 horas (depende de volume de dados e velocidade de índices)

**Risco:** Alto. Requer backup antes, monitoramento durante, plano de rollback preparado.

---

## Pré-requisitos

- [ ] Todas as migrações aplicadas (Alembic up-to-date)
- [ ] Backup de produção recente executado
- [ ] Scripts de validação testados em cópia de produção
- [ ] RLS validado sem vazamento (todos os 12 cenários de teste passaram)
- [ ] Índices candidatos medidos e aprovados (EXPLAIN ANALYZE OK)
- [ ] Performance baseline registrada (latência p50/p95, tamanho)
- [ ] Plano de rollback documentado
- [ ] Notificação aos stakeholders de janela de manutenção

---

## Fase 1: Preparação (Antes do Cutover)

### 1.1. Backup de Segurança

```bash
# Backup completo de produção
pg_dump -h prod-db.example.com -U postgres -d hub_prod --format=directory --jobs=4 \
  > /backups/hub_prod_pre_cutover_$(date +%Y%m%d_%H%M%S).backup

# Verificar tamanho e integridade
ls -lh /backups/hub_prod_pre_cutover_*
```

**Tempo esperado:** 30-60 minutos (depende de volume)

### 1.2. Validar Dados Antes do Cutover

Executar script de inventário e validação:

```sql
psql -h prod-db.example.com -U postgres -d hub_prod -f \
  backend/migrations/sql/0001-inventario-baseline.sql > /tmp/inventario_antes.txt

psql -h prod-db.example.com -U postgres -d hub_prod -f \
  backend/migrations/sql/0002-validacao-orfaos.sql > /tmp/validacao_antes.txt
```

**Verificar:**
- Nenhum órfão (relações inválidas)
- Nenhuma colisão de unicidade
- Contagens registradas para comparação pós-migração

Se há problemas: **ABORTAR cutover** e resolver antes.

### 1.3. Preparar Rollback

```bash
# Manter cópia dos scripts de downgrade à mão
cp backend/migrations/alembic/versions/downgrade_*.py /tmp/downgrade_backup/

# Documentar procedimento de rollback
cat > /tmp/rollback_procedure.txt << 'EOF'
ROLLBACK PROCEDURE
==================
1. Parar aplicação
2. RESTORE from backup:
   pg_restore -h prod-db.example.com -U postgres -d hub_prod /backups/hub_prod_pre_cutover_*.backup
3. Downgrade Alembic:
   alembic downgrade -1  (uma versão por vez se necessário)
4. Restart aplicação com código anterior
5. Validar: listar empresas, parceiros, negócios
EOF
```

---

## Fase 2: Executar Migração (Janela de Manutenção)

### 2.1. Anunciar Manutenção

- Notificar usuários: "Manutenção programada de 22:00 a 02:00"
- Parar tráfego de lote/importador
- Permitir apenas queries leitura (opcional, mais seguro: parar tudo)

### 2.2. Parar Aplicação

```bash
# Parar workers/gunicorn
systemctl stop hub-backend

# Verificar que nenhuma conexão ativa
psql -h prod-db.example.com -U postgres -d hub_prod -c \
  "SELECT pid, usename, query_start FROM pg_stat_activity WHERE datname = 'hub_prod';"
```

**Esperar:** Até que não haja conexões ativas.

### 2.3. Aplicar Migrações Alembic

```bash
cd backend
alembic upgrade head

# Validar que migrações foram aplicadas
alembic current
```

**Esperado:** Versão HEAD está aplicada.

### 2.4. Validar Após Migração

Executar os mesmos scripts de validação:

```sql
psql -h prod-db.example.com -U postgres -d hub_prod -f \
  backend/migrations/sql/0001-inventario-baseline.sql > /tmp/inventario_depois.txt

psql -h prod-db.example.com -U postgres -d hub_prod -f \
  backend/migrations/sql/0002-validacao-orfaos.sql > /tmp/validacao_depois.txt
```

**Comparar com antes:**
- Mesma contagem de linhas? (sim = bom)
- Nenhum órfão? (sim = bom)
- Todas as empresas têm empresa_id NOT NULL? (sim = bom)

Se há divergências: **ROLLBACK IMEDIATAMENTE** (seção 2.5)

### 2.5. Rollback de Emergência (se necessário)

```bash
# Downgrade Alembic (uma versão por vez se necessário)
alembic downgrade -1

# RESTORE de backup
pg_restore -h prod-db.example.com -U postgres -d hub_prod \
  /backups/hub_prod_pre_cutover_*.backup

# Parar e reiniciar aplicação com versão anterior
systemctl restart hub-backend

# Validar que dados estão íntegros
curl -s http://localhost:8000/api/v1/auth/eu -H "Authorization: Bearer $TOKEN" | jq '.nome'
```

---

## Fase 3: Ativar Isolamento no Backend

### 3.1. Deploy Novo Backend

O novo código backend:
- Resolve `X-Empresa-ID` obrigatoriamente
- Define contexto RLS `app.empresa_id` em cada requisição
- Bloqueia operações tenant-scoped sem empresa explícita

```bash
# Build nova imagem/pacote
docker build -t hub-backend:multi-tenant .

# Deploy (um servidor por vez para high availability)
docker stop hub-backend-1
docker run -d --name hub-backend-1 \
  -e HUB_DATABASE_URL=postgresql+psycopg://... \
  -e HUB_AMBIENTE=producao \
  --restart=always \
  hub-backend:multi-tenant

# Validar que started
sleep 5
curl -s http://localhost:8000/health

# Repetir para outros servidores
```

### 3.2. Deploy Frontend Novo

Frontend precisa:
- Usar `X-Empresa-ID` em todos os requests
- Permitir seleção de empresa ativa
- Listar empresas do usuário em `/auth/empresas`

```bash
npm run build
npm run deploy
# ou: aws s3 sync dist/ s3://hub-frontend/ --delete
```

### 3.3. Validações Rápidas em Produção

```bash
# Testar login
curl -X POST http://prod.api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@isolutis.com.br","senha":"..."}'

# Testar requisição com X-Empresa-ID
curl -H "Authorization: Bearer $TOKEN" \
  -H "X-Empresa-ID: uuid-empresa-1" \
  http://prod.api/parceiros | jq '.[] | .nome' | head -5

# Testar sem X-Empresa-ID (deve falhar)
curl -H "Authorization: Bearer $TOKEN" \
  http://prod.api/parceiros | jq '.detail'
# Esperado: erro sobre X-Empresa-ID obrigatório
```

---

## Fase 4: Monitoramento (12-24 horas)

### 4.1. Observability

Monitorar:
- Taxa de erro (deve estar próximo a 0%)
- Latência p50/p95 (deve estar perto do baseline)
- Consumo de memória/CPU (deve estar normal)
- Tamanho do pool de conexão (não deve estar crescendo)

```bash
# Exemplo: Grafana dashboard
# Verificar: error_rate, http_request_duration_seconds_bucket, db_connections_active

# Exemplo: Log agregador (ELK, Datadog, etc)
# Buscar: "empresa_id" para confirmar que está sendo validado
# Buscar: "SemPermissao" para verificar tentativas de acesso inválido
```

### 4.2. Testes Funcionais

Verificar:
- [ ] Usuário pode listar suas empresas `/auth/empresas`
- [ ] Usuário pode criar parceiro (empresa1) e não vê em empresa2
- [ ] Usuário pode alternar entre empresas (header X-Empresa-ID)
- [ ] Filtros, buscas, relatórios funcionam normalmente
- [ ] WebSocket/realtime conecta e funciona
- [ ] Importação legada (se existe) funciona

### 4.3. Performance Check

Comparar com baseline (antes de cutover):

```bash
python -m app.scripts.medir_performance > /tmp/performance_pos_cutover.txt

# Comparar p50/p95 com /tmp/performance_pre_cutover.txt
# Aceitável: até +10% de aumento
# Preocupante: +25% ou mais (pode indicar índices ineficientes ou RLS overhead)
```

Se performance degradada:
1. Rodar EXPLAIN ANALYZE (script 0005)
2. Verificar se há sequential scans inesperados
3. Se necessário, criar índice adicional (monitorar write amplification)
4. Se não conseguir otimizar: escalate para discussão arquitetônica

---

## Fase 5: Finalizar

### 5.1. Documentar Alterações

- Timestamp do cutover
- Versão do código aplicado
- Status de todas as validações
- Problemas encontrados e resolvidos
- Performance baseline pós-cutover

### 5.2. Comunicar Resultado

Avisar stakeholders:
- "Cutover de multi-tenant concluído com sucesso"
- "Sistema operacional em isolamento total por empresa"
- "Performance dentro do baseline esperado"

### 5.3. Desabilitar Rollback Automático

Depois de 24-48 horas com sistema estável:
- Remover procedures de rollback rápido (backup de pre-cutover pode ser arquivado)
- Documentar como fazer restore se necessário (processo longo)
- Atualizar runbooks para new architecture

---

## Tabela: Comparação Antes x Depois

```
Métrica                    Antes          Depois         Aceitável?
──────────────────────────────────────────────────────────────────
Parceiros listar p50       45 ms          48 ms          ✓ (<+10%)
Parceiros listar p95       150 ms         160 ms         ✓ (<+10%)
Negócios listar p50        60 ms          65 ms          ✓ (<+10%)
Negócios listar p95        200 ms         220 ms         ✓ (<+10%)
Receita período p50        80 ms          85 ms          ✓ (<+10%)
Receita período p95        300 ms         320 ms         ✓ (<+10%)
Tamanho de índices         2.5 GB         2.8 GB         ✓ (+10%)
Tamanho de dados           8.2 GB         8.2 GB         ✓ (igual)
Taxa de erro               < 0.1%         < 0.1%         ✓
Concorrência DB            15 conns       18 conns       ✓ (normal)
Memória app                512 MB         520 MB         ✓ (+1.5%)
```

---

## Plano B: Rollback Procedural

Se tudo der errado:

1. **Parar aplicação** (para evitar mais danos)
2. **Restore backup:**
   ```bash
   pg_restore -h prod-db.example.com -U postgres -d hub_prod \
     /backups/hub_prod_pre_cutover_*.backup
   ```
3. **Downgrade Alembic:**
   ```bash
   alembic downgrade -1
   # Repetir até versão anterior estável
   ```
4. **Deploy código anterior**
5. **Validar dados** (contagens, órf ãos)
6. **Reiniciar aplicação**
7. **Comunicar falha aos stakeholders**

**Tempo de rollback:** 1-2 horas (depende do volume de restore)

---

## Checklist Final

### Pré-Cutover
- [ ] Backup completo criado e testado
- [ ] Scripts de validação testados em cópia de produção
- [ ] RLS validado (12 cenários OK)
- [ ] Performance baseline registrada
- [ ] Rollback procedure documentado e testado
- [ ] Stakeholders notificados

### Durante Cutover
- [ ] Aplicação parada
- [ ] Migrações Alembic aplicadas com sucesso
- [ ] Validação após migração passou (contagens OK, órfãos=0)
- [ ] Backend novo deployado e testado
- [ ] Frontend novo deployado e testado
- [ ] Testes funcionais rápidos passaram

### Pós-Cutover (primeiras 24h)
- [ ] Monitoramento não mostra erros críticos
- [ ] Taxa de erro < 0.5%
- [ ] Latência p95 < +15% do baseline
- [ ] Testes funcionais completos passaram
- [ ] Performance check dentro do esperado

---

## Contatos de Emergência

- **DBA On-Call:** jefferson.webguirra@gmail.com
- **DevOps Lead:** [adicionado conforme necessário]
- **CTO/Arquiteto:** [adicionado conforme necessário]

Manter contatos atualizados e testados antes de iniciar cutover.

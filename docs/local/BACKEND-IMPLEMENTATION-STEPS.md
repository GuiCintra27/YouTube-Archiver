# Passo a passo (curto) — Fase 0 + Catálogo

Este arquivo é o “checklist” para irmos implementando em incrementos pequenos, reduzindo risco e evitando over-context.

## Regras do jogo

- Cada passo deve tocar poucos arquivos e gerar um resultado observável (ou um teste).
- Não alterar contratos de sucesso (2xx) sem necessidade.
- Tudo novo atrás de flag quando fizer sentido (`CATALOG_ENABLED`).

## Passos — Fase 0 (fundação)

1) **Baseline**
- Rodar `pytest` do backend e salvar estado atual (para garantir que o refactor não quebre coisas).

2) **Request ID (middleware + contexto)**
- Criar `app/core/request_context.py` (ContextVar).
- Criar `app/core/middleware/request_id.py`.
- Registrar middleware em `app/main.py`.

3) **Logging com request_id**
- Atualizar `app/core/logging.py` para injetar `request_id` no LogRecord e incluir no format.

4) **Erro padronizado com request_id**
- Atualizar `app/core/errors.py` (`ErrorResponse` com `request_id`).
- Garantir que handlers incluam request id no payload e log.

5) **Catch-all configurável**
- Adicionar setting em `app/config.py` (ex.: `ENABLE_GENERIC_EXCEPTION_HANDLER`).
- Registrar handler genérico em `register_exception_handlers()` quando habilitado.

6) **Unificar validações de path (compat)**
- Criar `app/core/paths.py` (source of truth).
- Fazer `app/core/security.py` virar wrapper/compat apontando para `paths.py`.

7) **(Opcional) Limpar try/except redundante**
- Remover `try/except Exception -> HTTPException(500)` onde não agrega valor (começar por `downloads/router.py`).

## Passos — Catálogo (com as decisões já fechadas)

8) **Criar módulo `catalog` (skeleton)**
- Criar `app/catalog/` (database/repository/service/schemas).
- Adicionar `CATALOG_DB_PATH=backend/database.db` + `CATALOG_ENABLED=false` em `app/config.py`.

9) **Criar schema do SQLite + init**
- Implementar DDL idempotente (tabelas `videos`, `assets`, `catalog_state`).
- Implementar `catalog/status` (counts + last import/publish).

10) **Bootstrap local (scan único)**
- Criar `POST /api/catalog/bootstrap-local` que:
  - faz scan do `downloads/` uma vez
  - popula `location=local`
- Não trocar `GET /api/videos` ainda.

11) **Ler catálogo local (feature-flag)**
- Quando `CATALOG_ENABLED=true`, `GET /api/videos` passa a ler do SQLite.
- Quando `false`, mantém scan/cache atual.

12) **Atualizar catálogo após operações locais**
- No delete/rename (library): atualizar registros do catálogo.
- Após download concluído: upsert do vídeo e assets no catálogo.

Nota (ambiente atual):
- Evitar executar handlers sync (`def`) no FastAPI, pois caem em threadpool (anyio) e aqui isso travou; preferir manter endpoints como `async def` mesmo quando a lógica interna for síncrona.

13) **Snapshot do Drive: formato e utilitários**
- Implementar gzip JSON (`catalog-drive.json.gz`) com `schema_version=1`.
- Implementar encode/decode e validação básica do schema.

14) **Import do snapshot do Drive**
- Criar `POST /api/catalog/drive/import`.
- Atualizar `location=drive` no SQLite a partir do snapshot.

15) **Drive list via catálogo (feature-flag)**
- Quando `CATALOG_ENABLED=true`, `GET /api/drive/videos` passa a ler do SQLite (`location=drive`).
- Quando `false`, manter fluxo atual temporariamente.

16) **Publish do snapshot do Drive (a cada ação)**
- Criar `POST /api/catalog/drive/publish`.
- Integrar nos fluxos do Drive:
  - após upload/delete/rename: atualizar SQLite e publicar snapshot.
- Regra operacional inicial: “import antes de publish” para reduzir overwrite.

16.1) **Bootstrap inicial do Drive (quando não existe snapshot)**
- Criar `POST /api/catalog/drive/rebuild` (job) para:
  - varrer o Drive uma vez
  - popular `location=drive` no SQLite
  - publicar `catalog-drive.json.gz`

17) **Desativar fluxo antigo (quando estável)**
- Remover fallback de listagem/busca no Drive.
- Tornar scan local “apenas bootstrap/manual resync”.
- Reavaliar o papel do `drive_cache.db` (possível deprecar).

## Status atual (implementado)

- ✅ Passos 2–6 (Fase 0): request id + logging + erros padronizados + catch-all configurável + `core/paths.py`.
- ✅ Passos 8–15: módulo `catalog`, schema SQLite, bootstrap local, listagem local/Drive via catálogo (feature-flag), import de snapshot do Drive.
- ✅ Passo 16: publish manual + integração de write-through/publish nas ações do Drive (upload/delete/rename/update thumbnail).
- ✅ Passo 16.1: bootstrap inicial do Drive via `POST /api/catalog/drive/rebuild` (cria snapshot quando ainda não existe).
- ✅ Passo 12 (parte “download concluído”): write-through do catálogo local após conclusão do download (captura de `filepath` no hook de progresso).

## Observações / desvios do plano

- Testes: neste workspace o `pytest` não está no `PATH`; usar `cd backend && ./.venv/bin/python -m pytest -q -k "not drive_cache"`.
- Passo 16 (policy “import antes de publish”): `publish_drive_snapshot()` bloqueia publish quando detecta snapshot existente e `last_imported_at` está vazio; override via `POST /api/catalog/drive/publish?force=true`.
- Uploads em batch: para evitar reupload do snapshot N vezes, a política atual publica **uma vez por job** (batch upload / external upload); ações unitárias publicam ao final da ação.
- Download do Drive: o `DriveManager.download_file()` foi migrado para **streaming via Drive REST API + `requests`** (sem `googleapiclient`/`BytesIO`) para evitar crash nativo (`double free or corruption (!prev)`); usa `.part` e valida tamanho esperado para não deixar arquivos parciais “silenciosos”.
- Job cleanup: foi necessário manter aliases compat (`jobs_db`/`active_tasks`) em `backend/app/jobs/store.py` para o loop de cleanup não quebrar.

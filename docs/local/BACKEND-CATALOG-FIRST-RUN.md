# Primeira execução — Catálogo (Drive sem snapshot ainda)

Se o seu Google Drive **já tem vídeos**, mas **ainda não existe** o arquivo `catalog-drive.json.gz`, siga este fluxo para “inicializar” o novo sistema.

## Objetivo

- Criar um catálogo local (`backend/database.db`) e, principalmente:
- Fazer **uma varredura única** no Drive para gerar e publicar `YouTube Archiver/.catalog/catalog-drive.json.gz`.
- Depois disso, `/api/drive/videos` passa a ser **instantâneo** (consulta no SQLite), sem busca/listagem recursiva no Drive.

## Passo a passo

1) Habilitar o catálogo no backend
- Em `backend/.env`:
  - `CATALOG_ENABLED=true`
  - (opcional) `CATALOG_DB_PATH=database.db`

2) Subir backend e autenticar no Drive
- Inicie com `cd backend && ./run.sh`
- Acesse `/api/drive/auth-url` e conclua o OAuth.

3) (Opcional) Popular catálogo local (scan único)
- `POST /api/catalog/bootstrap-local`

4) Inicializar catálogo do Drive (varredura única + publish do snapshot)
- `POST /api/catalog/drive/rebuild`
  - Retorna `job_id`
  - Acompanhe em `GET /api/jobs/{job_id}` até `status=completed`

5) Validar
- `GET /api/drive/videos` deve responder rápido e listar via catálogo.
- `GET /api/drive/sync-status` deve responder rápido (sem varredura do Drive).

## Para o painel de Sync (Local ↔ Drive)

O painel de sincronização depende dos **dois índices**:
- Drive: `POST /api/catalog/drive/rebuild` (primeira vez) ou `POST /api/catalog/drive/import` (máquina nova)
- Local: `POST /api/catalog/bootstrap-local`

Sem o catálogo local, o backend retorna `warnings` no `/api/drive/sync-status` e bloqueia operações em lote.

## Em uma máquina nova (já com snapshot existente)

- Rode `POST /api/catalog/drive/import` (baixa 1 arquivo e importa no SQLite).
- Não precisa varrer o Drive.

## Observações importantes

- Com `CATALOG_ENABLED=true`, se o catálogo do Drive estiver vazio, o backend **não faz fallback** para a listagem lenta (por default); retorna lista vazia com `warning`.
- `POST /api/catalog/drive/rebuild` é um endpoint “admin/one-off”; ele publica o snapshot com `force=true` (overwrite).

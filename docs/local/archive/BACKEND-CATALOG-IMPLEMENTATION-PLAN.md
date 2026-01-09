# Plano de Implementação — Catálogo (após Fase 0)

Este plano traduz o design do catálogo (`docs/local/BACKEND-CATALOG-DESIGN.md`) em passos executáveis no backend, com foco em **entregas pequenas**, reversíveis e testáveis.

## Princípio de rollout

- Introduzir o catálogo **em paralelo** ao comportamento atual.
- Migrar endpoints para ler do catálogo **por feature-flag** (config).
- Só remover o fluxo antigo (scan + Drive cache/list) após estabilizar.

## Fases do Catálogo

### Catálogo 1 — Persistência local + bootstrap

**Objetivo:** o backend passa a ter um índice local confiável, mas ainda pode usar o fluxo antigo como fallback.

**Mudanças**
- Adicionar módulo `backend/app/catalog/`:
  - `database.py`: conexão SQLite, migrations simples (DDL idempotente)
  - `repository.py`: consultas (listagem/paginação/busca)
  - `schemas.py`: modelos Pydantic para responses (opcional)
  - `service.py`: bootstrap (scan único), upsert após download/delete/rename
  - `router.py` (opcional no início): endpoints internos de status/sync
- Config:
  - `CATALOG_DB_PATH` (default: `backend/database.db`)
  - `CATALOG_ENABLED` (default `false` no início)
  - `CATALOG_BOOTSTRAP_ON_STARTUP` (default `false`)
- Bootstrap local:
  - reutilizar o scan atual apenas **uma vez** para preencher `location=local`.

**Integrações mínimas**
- No final de um download bem-sucedido: `catalog.service.upsert_local_video(...)`
- Em delete/rename da library: atualizar catálogo

**Critérios de aceite**
- Com `CATALOG_ENABLED=true`, `GET /api/videos` pode listar via SQLite (mesma paginação/shape).
- Sem flag, nada muda.

### Catálogo 2 — Snapshot do Drive (import)

**Objetivo:** listagem do Drive passa a ser **100% por catálogo** (sem busca/listagem de vídeos no Drive).

**Mudanças**
- Definir o artefato do Drive:
  - pasta: `YouTube Archiver/.catalog/`
  - arquivo: `catalog-drive.json.gz`
- Implementar:
  - `catalog.service.import_drive_catalog()`:
    - baixar o snapshot (1 arquivo) do Drive
    - validar `schema_version`
    - atualizar `location=drive` no SQLite
  - `catalog_state` atualizado com `generated_at`, file_id e (se disponível) `etag/revision`
- Migrar `drive/service.py:list_videos_paginated` para:
  - ler `location=drive` do catálogo quando `CATALOG_ENABLED=true`
  - fallback para fluxo atual quando desabilitado

**Critérios de aceite**
- `GET /api/drive/videos` não faz listagem/busca de vídeos na API do Drive (apenas usa catálogo local).
- Thumbnails/transcrições passam a depender de `drive_file_id` (já vindo do catálogo).

**Bootstrap inicial (quando ainda não existe snapshot)**
- `POST /api/catalog/drive/rebuild`:
  - faz uma varredura completa do Drive (one-off)
  - popula `location=drive` no SQLite
  - publica `catalog-drive.json.gz`

**Rollout sugerido (compatibilidade)**
- Durante a migração, permitir fallback para o comportamento antigo caso o catálogo do Drive esteja vazio, para não “sumir” a biblioteca existente até o primeiro import.
  - Status atual: por default, com `CATALOG_ENABLED=true`, o backend retorna vazio + `warning` quando o catálogo estiver vazio (evita request lento); o fallback pode ser reativado via `CATALOG_DRIVE_ALLOW_LEGACY_LISTING_FALLBACK=true`.

### Catálogo 3 — Snapshot do Drive (publish)

**Objetivo:** após operações que alteram o Drive (upload/delete/rename), o catálogo do Drive é atualizado e publicado.

**Mudanças**
- `catalog.service.publish_drive_catalog()`:
  - gerar JSON (somente `location=drive`) a partir do SQLite
  - comprimir gzip
  - upload/update do arquivo no Drive
  - (opcional) optimistic concurrency com ETag
- Política de publish:
  - primeira versão: **publicar a cada ação relevante** (upload/delete/rename)
  - melhoria futura: batch/debounce (se o snapshot crescer demais)

**Critérios de aceite**
- Após upload/delete, uma nova máquina consegue importar o catálogo e ver os itens sem varredura.

**Status de implementação**
- Endpoint manual: `POST /api/catalog/drive/publish` publica o snapshot a partir do SQLite.
- Integrado: ações do Drive (upload/delete/rename/update thumbnail) fazem write-through no SQLite (`location=drive`) e disparam publish (best-effort).
- Observação: uploads em batch/publicações pesadas publicam **uma vez por job** (para reduzir overhead).
- Observação de segurança: por default, publish bloqueia overwrite se já existe snapshot e nunca houve import (override com `force=true`).

### Catálogo 4 — Desativar o fluxo antigo

**Objetivo:** remover dependências que viraram legado:
- scan por request (ficar só bootstrap/manual resync)
- `drive_cache.db` como fonte de listagem

**Mudanças**
- Marcar endpoints/paths antigos como deprecated internamente.
- Remover fallback (quando estável).

## Endpoints de suporte (recomendados)

Criar endpoints internos (podem ficar “ocultos” da UI inicialmente):

- `GET /api/catalog/status`
  - db path, counts por location, last import/publish, schema_version
- `POST /api/catalog/bootstrap-local`
  - roda scan único e popula `location=local`
- `POST /api/catalog/drive/import`
  - baixa snapshot do Drive e atualiza `location=drive`
- `POST /api/catalog/drive/publish`
  - publica snapshot do Drive (se autenticado)

Esses endpoints facilitam debug e migração sem “mágica” em startup.

## Testes (mínimos)

- Unit tests de `catalog.repository` (paginação e filtros).
- Integração via TestClient:
  - `CATALOG_ENABLED=true` + db temporário → `GET /api/videos` retorna shape esperado.
- “Golden file” para import do catálogo do Drive:
  - um `catalog-drive.json` pequeno e determinístico, validando parsing.

## Riscos e mitigação

- **Arquivo grande**: gzip + limitar payload do snapshot (sem campos desnecessários).
- **Overwrite ao trocar de máquina**: regra “import antes de publish” + (futuro) ETag.
- **Dados divergentes (Drive mudou fora do app)**:
  - opcional: endpoint “rebuild do Drive” que faz uma varredura completa (admin/one-off).

# Design — Catálogo de Vídeos (Local SQLite + Snapshot no Drive)

Este documento ajusta o planejamento de arquitetura do backend para suportar uma mudança estrutural: **parar de depender de “scan do disco” e “listagem/busca no Drive” como fonte de verdade**, e passar a usar um **catálogo persistido**.

## Objetivos

- Listagem/pesquisa de vídeos em O(1) / O(log n) via **SQLite local**, mesmo com 10.000+ vídeos.
- Eliminar a necessidade de percorrer pastas localmente a cada request (reduzir I/O e latência).
- Eliminar a necessidade de “buscar” vídeos no Drive (reduzir chamadas à API e erros intermitentes de thumb/transcrição).
- Permitir “troca de máquina” (concurrency limitada): uma nova máquina baixa o catálogo do Drive e consegue navegar/streamar vídeos do Drive sem varredura.

## Premissas e constraints

- Não há múltiplos usuários escrevendo simultaneamente na mesma biblioteca com frequência (mas pode haver troca de máquina).
- O catálogo do Drive será um **artefato autoritativo para os itens no Drive**.
- O backend ainda precisa manter:
  - streaming com Range Requests (206)
  - headers com RFC 5987 para Unicode
  - rate limiting
  - sem DRM

## Estratégia recomendada (incremental)

### V1 (prioridade): snapshot único comprimido no Drive + índice SQLite local

- **Local**: SQLite (`database.db`) como índice consultável pelo backend.
- **Drive**: um arquivo snapshot (`catalog-drive.json.gz`) armazenado na pasta raiz do projeto no Drive (ex.: `YouTube Archiver/.catalog/catalog-drive.json.gz`).
- **Sync**:
  - Download do snapshot → importar/atualizar as entradas `location=drive` no SQLite local.
  - Upload (publish) do snapshot → regenerar snapshot a partir do SQLite local (apenas itens `location=drive`) e enviar ao Drive.

Isso remove completamente a necessidade de “listar vídeos do Drive” para o usuário final. A única dependência de Drive API fica em:
- download/upload do(s) arquivo(s) de catálogo
- operações normais (upload vídeo, stream vídeo por `file_id`, etc.)

### V2 (opcional): snapshot + eventos (JSONL) para updates incrementais

Quando houver necessidade de evitar reupload de snapshot grande a cada alteração, evoluir para:
- `catalog-drive.snapshot.json.gz` (estado compactado)
- `catalog-drive.events.jsonl.gz` (append-only de mudanças)
- compaction periódica (job)

V1 é suficiente para começar e já resolve latência/erros da “busca no Drive”.

## Modelo de dados (conceitual)

### Entidades

**Video**
- `video_uid` (string, chave estável): preferir:
  - YouTube: `yt:<video_id>`
  - Playlist item: ainda `yt:<video_id>`
  - HLS/custom: `custom:<hash>` ou `custom:<archive_id>`
- `title`, `channel`, `duration_seconds`, `created_at`, `modified_at`
- `source` (enum): `youtube | hls | custom`
- `location` (enum): `local | drive`
- `status` (enum): `available | missing | pending | error`
- `tags` (opcional), `metadata` (JSON)

**Asset** (arquivo relacionado)
- `asset_uid` (string) ou PK numérica
- `video_uid` (FK)
- `kind` (enum): `video | thumbnail | subtitles | transcript | info_json | audio | other`
- `mime_type`, `size_bytes`, `sha256`/`md5` (opcional)
- `local_path` (relativo ao downloads dir) se `location=local`
- `drive_file_id` se `location=drive`
- `drive_md5`/`drive_modified_time` (opcional)

### Esquema SQLite (proposta)

Tabela `videos`
- `video_uid` TEXT PRIMARY KEY
- `location` TEXT NOT NULL
- `source` TEXT NOT NULL
- `title` TEXT
- `channel` TEXT
- `duration_seconds` INTEGER
- `created_at` TEXT
- `modified_at` TEXT
- `status` TEXT NOT NULL
- `extra_json` TEXT (JSON)

Índices recomendados:
- `(location, modified_at DESC)`
- `(location, title)`
- `(channel)`

Tabela `assets`
- `id` INTEGER PRIMARY KEY
- `video_uid` TEXT NOT NULL
- `location` TEXT NOT NULL
- `kind` TEXT NOT NULL
- `local_path` TEXT
- `drive_file_id` TEXT
- `mime_type` TEXT
- `size_bytes` INTEGER
- `hash` TEXT
- `extra_json` TEXT

Índices recomendados:
- `(video_uid, kind)`
- `(location, kind)`
- `(drive_file_id)` UNIQUE (onde aplicável)

Tabela `catalog_state`
- `scope` TEXT PRIMARY KEY (`drive` / `local`)
- `version` INTEGER
- `last_imported_at` TEXT
- `last_published_at` TEXT
- `drive_catalog_file_id` TEXT (opcional)
- `drive_catalog_etag` TEXT (opcional)
- `drive_catalog_revision` TEXT (opcional)

## Formato do snapshot no Drive (V1)

Arquivo: `catalog-drive.json.gz`

Conteúdo (JSON):
```json
{
  "schema_version": 1,
  "generated_at": "2025-12-23T12:00:00Z",
  "library_id": "optional-stable-id",
  "videos": [
    {
      "video_uid": "yt:dQw4w9WgXcQ",
      "title": "...",
      "channel": "...",
      "duration_seconds": 228,
      "modified_at": "...",
      "assets": [
        {"kind": "video", "drive_file_id": "1abc...", "mime_type": "video/mp4"},
        {"kind": "thumbnail", "drive_file_id": "1def...", "mime_type": "image/jpeg"},
        {"kind": "transcript", "drive_file_id": "1ghi...", "mime_type": "text/vtt"}
      ]
    }
  ]
}
```

Observações:
- snapshot do Drive deve carregar apenas o necessário para UI: paginação, thumb, stream.
- campos grandes (ex.: descrição completa) podem ficar em `extra_json` ou omitidos.

## Concorrência e conflitos (troca de máquina)

Mesmo sem uso simultâneo frequente, existe risco de “overwrite”:
- Máquina A publica snapshot antigo e apaga itens que só existiam no snapshot mais novo da Máquina B.

Mitigação recomendada (V1):
- **Optimistic concurrency** com ETag/revision:
  - Ao publicar: baixar snapshot atual + capturar `etag`/`revision`.
  - Gerar novo snapshot aplicando delta local sobre o snapshot baixado (merge).
  - Upload com precondition `If-Match: <etag>`. Se falhar (412), repetir (re-download e merge).
- Se não quiser ETag inicialmente: impor regra operacional:
  - “antes de publicar, sempre fazer import do Drive”
  - e logar `warning` se o snapshot local estiver desatualizado (comparar `generated_at`).

Mitigação futura (V2):
- usar JSONL append-only de eventos (reduz risco de overwrite).

## Fluxos principais (como isso muda a aplicação)

### Listagem de vídeos local
- Antes: scan + cache TTL.
- Depois: query no SQLite (`location=local`) com paginação/ordenação.
- Atualização do catálogo local:
  - no final de um download bem-sucedido: inserir/atualizar `videos` + `assets`.
  - em delete/rename: atualizar linhas correspondentes.

### Listagem de vídeos do Drive
- Antes: cache sqlite dedicado + fallback API / listagem direta.
- Depois: query no SQLite (`location=drive`) alimentado pelo snapshot importado.
- Atualização do catálogo do Drive:
  - após upload/delete/rename no Drive: atualizar SQLite e marcar “dirty” para publicar snapshot.
  - publicar snapshot:
    - imediato (simples) ou em batch (melhor UX e menos I/O).

### Thumbnails/transcrições no Drive
- UI precisa apenas do `drive_file_id` correto.
- O backend para `/api/drive/thumbnail/{file_id}` deixa de depender de “buscar por nome/estrutura”; ele usa ID diretamente (armazenado no catálogo).

## Migração (do estado atual para o catálogo)

### Passo 1 — Criar DB e schema (local)
- Definir caminho do DB (ex.: `backend/database.db` ou `./database.db` configurável).
- Criar tabelas e índices.

### Passo 2 — Bootstrap do catálogo local
- Executar um “scan único” do `downloads/` para popular `location=local`.
- Após isso, listagem normal não varre mais o disco.

### Passo 3 — Bootstrap do catálogo do Drive
Opções:
1) Se já existe o `drive_cache.db` com metadados suficientes:
   - gerar o snapshot do Drive a partir do cache e publicar uma vez.
2) Se não existe catálogo:
   - fazer uma “sync inicial” usando Drive API (uma vez) para montar snapshot.
3) Manual:
   - apenas começar a criar catálogo do Drive a partir de novos uploads (Drive antigo fica “invisível” até importar).

## Impacto no roadmap de arquitetura

- A Fase 0 (erros/logging/request_id) continua altamente recomendada antes da migração do catálogo.
- A “evolução do jobs engine” deve considerar:
  - jobs de sync/publish do catálogo
  - jobs de compaction (se V2)

## Perguntas em aberto (para fechar antes da implementação)

Decisões tomadas:

1) DB local: `backend/database.db` (configurável, mas esse é o default do projeto).
2) O catálogo do Drive inclui **apenas itens do Drive** (`location=drive`). Itens locais só ficam “multidispositivo” quando o usuário fizer upload para o Drive.
3) Política de publicação: **publicar a cada ação** que altere o estado (upload/delete/rename). Objetivo é consistência e simplicidade; otimizações (batch/debounce) ficam para depois.

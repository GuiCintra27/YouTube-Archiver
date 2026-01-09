# YT-Archiver - Architecture Overview

## Objetivo

Documentar a arquitetura do YT-Archiver para facilitar entendimento tecnico, onboarding e apresentacao para recrutadores.

## Visao Geral

O projeto e um monorepo full-stack com tres blocos principais:

- **Frontend (Next.js 15)**: UI com SSR/ISR, cache por tags e componentes client para interacoes.
- **Backend (FastAPI)**: API modular com jobs em background, catalogo SQLite e integracao com Google Drive.
- **Infra local (opcional)**: Observabilidade com Prometheus + Grafana via Docker Compose.

```
[Usuario] -> [Frontend Next.js] -> [Backend FastAPI] -> [yt-dlp | SQLite | Google Drive]
                                  \-> [Prometheus metrics]
```

## Backend (FastAPI)

### Camadas principais

- **Router**: expoe endpoints e valida entrada (Pydantic).
- **Service**: regras de negocio, orquestracao de catalogo e Drive.
- **Manager/Adapters**: integracoes externas (yt-dlp, Google Drive).
- **Catalogo**: SQLite + snapshot para listagem rapida.

### Modulos

- `downloads/`: download de videos, playlists e metadata via yt-dlp.
- `jobs/`: controle de jobs assincronos com progresso.
- `library/`: streaming local, thumbnails e metadados.
- `drive/`: auth, upload, sync, rename, share, thumbnails.
- `recordings/`: upload de gravacoes do browser.
- `catalog/`: persistencia e reconciliacao local <-> Drive.

### Fluxos criticos

**Download (video/playlist)**
1. Frontend solicita `/api/download`.
2. Backend cria job e inicia yt-dlp.
3. A cada progresso, job atualiza status.
4. Catalogo escreve o item e sidecars (thumbnails, legendas).

**Sync local -> Drive**
1. Frontend dispara `/api/drive/sync-all`.
2. Backend compara catalogo local vs Drive.
3. Uploads usam resumable upload com retry e backoff.
4. Catalogo e cache do Drive atualizam estado.

### Persistencia

- **SQLite local** para catalogo principal.
- **Drive cache** (opcional) para reduzir custo de listagens.
- **Sidecars** para thumbnails, legendas e metadados.

## Frontend (Next.js 15)

### Estrutura

- **App Router** com Server Components por default.
- **Client Components** para interacoes (download, sync, gravacao).
- **Cache tags** para invalidacao seletiva (listas e detalhes).

### Pilares

- **SSR/ISR**: render inicial com dados do backend.
- **Cache por tags**: invalidacao via route handlers.
- **Componentes por dominio**: `home/`, `library/`, `drive/`, `record/`.

### Fluxo de dados

1. Server Components chamam backend via `lib/server/api.ts`.
2. Cache tags mantem listas consistentes.
3. Acoes do usuario disparam revalidate + eventos client-side.

## Observabilidade (opcional)

- **/metrics** expoe Prometheus metrics.
- **Grafana** com dashboards para API, jobs, downloads e Drive.
- Stack isolada em `docker-compose.observability.yml`.

## Decisoes de arquitetura

- **Monorepo** para coesao e demo completa.
- **FastAPI + Pydantic** por produtividade e validacao robusta.
- **Next.js App Router** para SSR e cache nativo.
- **SQLite** por simplicidade, portabilidade e leitura rapida.

## Referencias

- `docs/project/TECHNICAL-REFERENCE.md`
- `docs/project/OBSERVABILITY.md`
- `docs/project/GOOGLE-DRIVE-FEATURES.md`
- `docs/project/GLOBAL-PLAYER.md`

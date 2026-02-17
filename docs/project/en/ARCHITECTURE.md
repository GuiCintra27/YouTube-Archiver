# YT-Archiver - Architecture Overview

[PT-BR](../ARCHITECTURE.md) | **EN**

## Objective

Document the YT-Archiver architecture to facilitate technical understanding, onboarding and presentation to recruiters.

## Overview

The project is a full-stack monorepo with three main blocks:

- **Frontend (Next.js 15)**: interface with SSR/ISR, tag cache and client components for interactions.
- **Backend (FastAPI)**: Modular API with background jobs, SQLite catalog and integration with Google Drive.
- **Local infrastructure (optional)**: Observability with Prometheus + Grafana via Docker Compose.

```
[Usuário] -> [Frontend Next.js] -> [Backend FastAPI] -> [yt-dlp | SQLite | Google Drive]
                                  \-> [Prometheus metrics]
```

## Backend (FastAPI)

### Main layers

- **Router**: exposes endpoints and validates input (Pydantic).
- **Service**: business rules, catalog and Drive orchestration.
- **Manager/Adapters**: external integrations (yt-dlp, Google Drive).
- **Catalog**: SQLite + snapshot for quick listing.

### Modules

- `downloads/`: download videos, playlists and metadata via yt-dlp.
- `jobs/`: control of asynchronous jobs with progress.
- `library/`: local streaming, thumbnails and metadata.
- `drive/`: auth, upload, sync, rename, share, thumbnails.
- `recordings/`: uploading recordings from the browser.
- `catalog/`: persistence and local reconciliation <-> Drive.

### Critical flows

**Download (video/playlist)**
1. Frontend requests `/api/download`.
2. Backend creates job and starts yt-dlp.
3. With each progress, job updates status.
4. Catalog writes the item and sidecars (thumbnails, captions).

**Local Sync -> Drive**
1. Frontend fires `/api/drive/sync-all`.
2. Backend compares local catalog vs Drive.
3. Uploads use summary shipping with retry and backoff.
4. Drive catalog and cache update state.

### Persistence

- **Local SQLite** for main catalog.
- **Drive cache** (optional) to reduce listing costs.
- **Sidecars** for thumbnails, captions and metadata.

## Frontend (Next.js 15)

### Structure

- **App Router** with Server Components by default.
- **Client Components** for interactions (download, sync, recording).
- **Cache tags** for selective invalidation (lists and details).

### Pillars

- **SSR/ISR**: initial render with backend data.
- **Cache by tags**: invalidation via route handlers.
- **Components per domain**: `home/`, `library/`, `drive/`, `record/`.

### Data flow

1. Server Components call the backend via `lib/server/api.ts`.
2. Cache tags keep lists consistent.
3. User actions trigger revalidate + client-side events.

## Observability (optional)

- **/metrics** exposes Prometheus metrics.
- **Grafana** with dashboards for API, jobs, downloads and Drive.
- Stack isolated in `docker-compose.observability.yml`.

## Architectural decisions

- **Monorepo** for cohesion and full demo.
- **FastAPI + Pydantic** for productivity and robust validation.
- **Next.js App Router** for SSR and native caching.
- **SQLite** for simplicity, portability and fast reading.

## References

- `docs/project/TECHNICAL-REFERENCE.md`
- `docs/project/OBSERVABILITY.md`
- `docs/project/GOOGLE-DRIVE-FEATURES.md`
- `docs/project/GLOBAL-PLAYER.md`

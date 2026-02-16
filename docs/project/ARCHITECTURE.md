# YT-Archiver - Visão Geral da Arquitetura

## Objetivo

Documentar a arquitetura do YT-Archiver para facilitar entendimento técnico, onboarding e apresentação para recrutadores.

## Visão Geral

O projeto é um monorepo full-stack com três blocos principais:

- **Frontend (Next.js 15)**: interface com SSR/ISR, cache por tags e componentes client para interações.
- **Backend (FastAPI)**: API modular com jobs em background, catálogo SQLite e integração com Google Drive.
- **Infra local (opcional)**: Observabilidade com Prometheus + Grafana via Docker Compose.

```
[Usuário] -> [Frontend Next.js] -> [Backend FastAPI] -> [yt-dlp | SQLite | Google Drive]
                                  \-> [Prometheus metrics]
```

## Backend (FastAPI)

### Camadas principais

- **Router**: expõe endpoints e valida entrada (Pydantic).
- **Service**: regras de negócio, orquestração de catálogo e Drive.
- **Manager/Adapters**: integrações externas (yt-dlp, Google Drive).
- **Catálogo**: SQLite + snapshot para listagem rápida.

### Módulos

- `downloads/`: download de vídeos, playlists e metadados via yt-dlp.
- `jobs/`: controle de jobs assíncronos com progresso.
- `library/`: streaming local, thumbnails e metadados.
- `drive/`: auth, upload, sync, rename, share, thumbnails.
- `recordings/`: upload de gravações do browser.
- `catalog/`: persistência e reconciliação local <-> Drive.

### Fluxos críticos

**Download (vídeo/playlist)**
1. Frontend solicita `/api/download`.
2. Backend cria job e inicia yt-dlp.
3. A cada progresso, job atualiza status.
4. Catálogo escreve o item e sidecars (thumbnails, legendas).

**Sync local -> Drive**
1. Frontend dispara `/api/drive/sync-all`.
2. Backend compara catálogo local vs Drive.
3. Uploads usam envio resumível com retry e backoff.
4. Catálogo e cache do Drive atualizam estado.

### Persistência

- **SQLite local** para catálogo principal.
- **Drive cache** (opcional) para reduzir custo de listagens.
- **Sidecars** para thumbnails, legendas e metadados.

## Frontend (Next.js 15)

### Estrutura

- **App Router** com Server Components por padrão.
- **Client Components** para interações (download, sync, gravação).
- **Cache tags** para invalidação seletiva (listas e detalhes).

### Pilares

- **SSR/ISR**: render inicial com dados do backend.
- **Cache por tags**: invalidação via route handlers.
- **Componentes por domínio**: `home/`, `library/`, `drive/`, `record/`.

### Fluxo de dados

1. Server Components chamam o backend via `lib/server/api.ts`.
2. Cache tags mantêm listas consistentes.
3. Ações do usuário disparam revalidate + eventos client-side.

## Observabilidade (opcional)

- **/metrics** expõe métricas Prometheus.
- **Grafana** com dashboards para API, jobs, downloads e Drive.
- Stack isolada em `docker-compose.observability.yml`.

## Decisões de arquitetura

- **Monorepo** para coesão e demo completa.
- **FastAPI + Pydantic** por produtividade e validação robusta.
- **Next.js App Router** para SSR e cache nativo.
- **SQLite** por simplicidade, portabilidade e leitura rápida.

## Referências

- `docs/project/TECHNICAL-REFERENCE.md`
- `docs/project/OBSERVABILITY.md`
- `docs/project/GOOGLE-DRIVE-FEATURES.md`
- `docs/project/GLOBAL-PLAYER.md`

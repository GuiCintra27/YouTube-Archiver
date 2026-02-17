# Quick Technical Reference - YT-Archiver

[PT-BR](../TECHNICAL-REFERENCE.md) | **EN**

Quick reference guide for development and troubleshooting.

**Index:** **[INDEX.md](./INDEX.md)**

**Last updated:** 2026-01-09

---

## 🏗️ Architecture at a Glance

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Frontend      │         │    Backend      │         │  Google Drive   │
│   Next.js 15    │────────▶│    FastAPI      │────────▶│   Drive API     │
│   Port 3000     │  HTTP   │   Port 8000     │  OAuth  │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        │                           │
        │                           │
        ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│   shadcn/ui     │         │    yt-dlp       │
│   Tailwind CSS  │         │    ffmpeg       │
└─────────────────┘         └─────────────────┘
```

---

## 🔧 Complete Technical Stack

### Backend
| Component | Technology | Version | Usage |
|------------|-----------|---------|-----|
| Framework | FastAPI | 0.115+ | REST API |
| Server | Uvicorn | 0.32+ | ASGI server |
| Validation | Pydantic | 2.9+ | Request/response models |
| Download | yt-dlp | 2024.07+ | Video downloader |
| OAuth | google-auth-oauthlib | 1.2+ | Google Drive authentication |
| Drive API | google-api-python-client | 2,137+ | Drive operations |
| SQLite Cache | aiosqlite | 0.19+ | Drive cache access |
| Observability | prometheus-client | 0.20+ | Endpoint Metrics |
| Jobs store (optional) | redis | 5.0+ | Shared job backend |
| Catalog DB | SQLite | Built-in | Persistent catalog (local + drive) |
| Runtime | Python | 3.12+ | Backend runtime |

### Frontend
| Component | Technology | Version | Usage |
|------------|-----------|---------|-----|
| Framework | Next.js | 15.0.5 | React framework |
| UI Library | shadcn/ui | Latest | Component library |
| CSS | Tailwind CSS | 3.4.17 | Styling |
| Video Player | Vidstack | 1.12.13 | HTML5player |
| Icons | Lucide React | 0.468+ | Icon system |
| Linter | ESLint | 9.39.1 | Flat config |
| Runtime | Node.js | 18+ | Frontend runtime |

---

## 📁 Critical Files Map

### Backend (Python) - Modular Architecture

```
backend/app/
├── main.py                         # ⭐ Entry point FastAPI + routers + /metrics
├── config.py                       # Configurações globais (Settings)
│
├── core/                           # Shared core module
│   ├── logging.py                  # ⭐ Logger estruturado + request_id
│   ├── metrics.py                  # ⭐ Prometheus metrics
│   ├── middleware/                 # Middleware HTTP (metrics/context)
│   ├── blocking.py                 # ⭐ Blocking I/O offload (to_thread)
│   ├── validators.py               # ⭐ URL, path and filename validation
│   ├── paths.py                    # Helpers de paths
│   ├── request_context.py          # Request ID/context
│   └── rate_limit.py               # Rate limiting with slowapi
│
├── catalog/                        # Persistent catalog (SQLite)
│   ├── router.py                   # Endpoints /api/catalog/*
│   ├── service.py                  # Catalog rules
│   ├── repository.py               # SQLite access
│   ├── database.py                 # Schema and connections
│   ├── drive_snapshot.py           # Snapshot drive (catalog-drive.json.gz)
│   └── identity.py                 # Catalog identity and hashing
│
├── downloads/                      # Downloads module
│   ├── router.py                   # Endpoints /api/download, /api/video-info
│   ├── service.py                  # Business logic
│   ├── schemas.py                  # ⭐ DownloadRequest (Pydantic)
│   └── downloader.py               # ⭐ Engine yt-dlp wrapper
│       ├── Settings (dataclass):   Download settings
│       ├── Downloader.download():  Main method
│       └── _base_opts():           yt-dlp options
│
├── jobs/                           # Async jobs module
│   ├── router.py                   # Endpoints /api/jobs/*
│   ├── service.py                  # Jobs management
│   ├── schemas.py                  # Job models
│   ├── store.py                    # Storage (memory/redis)
│   └── cleanup.py                  # ⭐ Automatic cleanup of old jobs
│
├── library/                        # Local library module
│   ├── router.py                   # ⭐ Endpoints /api/videos/* (streaming)
│   ├── service.py                  # Directory scan
│   ├── schemas.py                  # Video models
│   └── cache.py                    # ⭐ Directory scan cache (TTL 30s)
│
├── recordings/                     # Recordings module
│   ├── router.py                   # Endpoint /api/recordings/upload
│   ├── service.py                  # Recording persistence
│   └── schemas.py                  # Recording models
│
└── drive/                          # Google Drive module
    ├── router.py                   # Endpoints /api/drive/*
    ├── service.py                  # Business logic
    ├── schemas.py                  # Drive models
    ├── manager.py                  # ⭐ DriveManager
    └── cache/                      # Cache SQLite (opcional)
        ├── database.py             # Schema e conexão
        ├── repository.py           # CRUD de cache
        ├── sync.py                 # Full/incremental sync
        └── background.py           # Task periódica de sync

backend/
├── tests/                          # ⭐ Testes automatizados (pytest)
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   ├── e2e/                         # End-to-end tests
│   └── conftest.py                 # Fixtures compartilhadas
├── requirements.txt                # Dependências Python
├── pytest.ini                      # Configuração do pytest
├── .env.example                    # ⭐ Exemplo de variáveis de ambiente
├── run.sh                          # ⭐ Script de inicialização
├── credentials.json.example        # Template de credenciais
├── database.db                     # Catálogo SQLite (gitignored)
└── drive_cache.db                  # Cache SQLite do Drive (opcional)
```

### Frontend (TypeScript/React)

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx                    # ⭐ Main page (downloads)
│   │   ├── drive/page.tsx              # ⭐ Google Drive page
│   │   ├── library/page.tsx            # Video library
│   │   ├── record/page.tsx             # Screen recording
│   │   ├── layout.tsx                  # ⭐ Layout global
│   │   └── globals.css                 # Tailwind styles
│   │
│   ├── components/
│   │   ├── common/                     # Shared components
│   │   │   ├── error-boundary.tsx      # ⭐ Error Boundary with retry
│   │   │   ├── navigation.tsx          # Navigation menu
│   │   │   ├── providers.tsx           # Providers (tema/estado)
│   │   │   ├── theme-provider.tsx      # Tema dark/light
│   │   │   ├── theme-toggle.tsx        # Theme toggle
│   │   │   ├── pagination/             # Pagination controls
│   │   │   │   ├── index.ts
│   │   │   │   └── pagination-controls.tsx
│   │   │   └── videos/                 # VideoCard, VideoPlayer, RecentVideos
│   │   ├── drive/                      # Componentes Google Drive
│   │   │   ├── drive-auth.tsx
│   │   │   ├── drive-page-client.tsx
│   │   │   ├── drive-page-section.tsx
│   │   │   ├── drive-page-skeleton.tsx
│   │   │   ├── drive-video-grid.tsx
│   │   │   ├── external-upload-modal.tsx
│   │   │   └── sync-panel.tsx
│   │   ├── home/                       # Componentes da Home
│   │   │   ├── download-form.tsx       # ⭐ Formulário de download
│   │   │   └── recent-videos-section.tsx
│   │   ├── library/                    # Componentes da Biblioteca
│   │   │   ├── library-grid-section.tsx
│   │   │   ├── library-grid-skeleton.tsx
│   │   │   └── paginated-video-grid.tsx
│   │   ├── record/                     # Screen recording
│   │   │   ├── record-page-client.tsx
│   │   │   ├── screen-recorder.tsx
│   │   │   └── screen-recorder-loading.tsx
│   │   └── ui/                         # shadcn/ui (30+ componentes)
│   │
│   ├── hooks/                          # ⭐ Hooks customizados
│   │   ├── index.ts                    # Barrel export
│   │   ├── use-api-url.ts              # ⭐ URL da API (SSR-safe)
│   │   └── use-fetch.ts                # Fetch com AbortController
│   │
│   └── lib/
│       ├── api-config.ts               # Config da API (client/server)
│       ├── api-client.ts               # Cliente HTTP tipado
│       ├── api-urls.ts                 # Constantes de endpoints
│       ├── paths.ts                    # Rotas do app
│       ├── url-validator.ts            # Validação de URLs
│       ├── client/api.ts               # Cliente HTTP (frontend)
│       ├── server/api.ts               # Fetch SSR + cache tags
│       ├── server/route-utils.ts       # Proxy + revalidate helpers
│       ├── server/tags.ts              # Tags de cache
│       └── utils.ts                    # cn(), formatBytes()
│
├── eslint.config.mjs                   # ⭐ ESLint 9 flat config
├── package.json
├── next.config.ts
├── tailwind.config.ts
└── docs/local/
    └── IMPROVEMENTS.md                 # Status das melhorias
```

---

## 🔑 Endpoints HTTP Cheat Sheet

### Health and Information
```bash
GET  /                              # Health check
GET  /api/health                    # Health check detalhado
GET  /metrics                       # Prometheus metrics
GET  /docs                          # API docs (Swagger)
```

### Downloads
```bash
POST /api/download                  # Inicia download
POST /api/video-info                # Info without download
```

### Jobs
```bash
GET  /api/jobs                      # List jobs
GET  /api/jobs/{id}                 # Job status
GET  /api/jobs/{id}/stream          # Progress stream (SSE)
POST /api/jobs/{id}/cancel          # Cancel job
DELETE /api/jobs/{id}               # Remove job
```

### Local Library
```bash
GET  /api/videos                    # List videos
GET  /api/videos/stream/{path}      # Stream (206)
GET  /api/videos/thumbnail/{path}   # Thumbnail
PATCH /api/videos/rename/{path}     # Rename video
POST /api/videos/update-thumbnail/{path} # Atualizar thumbnail
POST /api/videos/delete-batch       # Batch delete
DELETE /api/videos/{path}           # Delete video
```

### Recordings
```bash
POST /api/recordings/upload         # Recording upload
```

### Catalog (SQLite)
```bash
GET  /api/catalog/status            # Catalog status
POST /api/catalog/bootstrap-local   # Index local videos
POST /api/catalog/drive/import      # Import Drive snapshot
POST /api/catalog/drive/publish     # Publish snapshot to Drive
POST /api/catalog/drive/rebuild     # Rebuild catalog by reading Drive
```

### Google Drive
```bash
GET  /api/drive/auth-status         # Check auth
GET  /api/drive/auth-url            # URL OAuth
GET  /api/drive/oauth2callback      # Callback OAuth
GET  /api/drive/videos              # List videos
POST /api/drive/upload/{path}       # Upload individual
POST /api/drive/upload-external     # Upload externo
POST /api/drive/sync-all            # Upload em lote
GET  /api/drive/sync-status         # Status sync
GET  /api/drive/sync-items          # Itens paginados (diff)
PATCH /api/drive/videos/{id}/rename # Rename video
POST /api/drive/videos/{id}/thumbnail # Atualizar thumbnail
GET  /api/drive/stream/{id}         # Stream (206)
GET  /api/drive/thumbnail/{id}      # Thumbnail
GET  /api/drive/custom-thumbnail/{id} # Thumbnail custom
DELETE /api/drive/videos/{id}       # Remove video + related files (returns cleanup_job_id)
POST /api/drive/videos/delete-batch # Batch delete
GET  /api/drive/videos/{id}/share   # Share status
POST /api/drive/videos/{id}/share   # Enable share
DELETE /api/drive/videos/{id}/share # Disable share
POST /api/drive/download            # Download (Drive -> local)
POST /api/drive/download-all        # Download em lote (Drive -> local)
POST /api/drive/cache/sync          # Sincroniza cache
GET  /api/drive/cache/stats         # Status do cache
POST /api/drive/cache/rebuild       # Rebuild do cache
DELETE /api/drive/cache             # Limpa cache
```

---

## 🐛 Bugs Fixed (cheat sheet)

### BUG #1: Local Video Streaming (FIXED ✅)
**Error:** `UnicodeEncodeError: 'latin-1' codec can't encode character '\u29f8'`
**File:** `backend/app/library/router.py` (function `stream_video`)
**Fix:**
```python
from urllib.parse import quote
encoded_filename = quote(full_path.name)
headers = {
    "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
}
```

### BUG #2: Drive Upload (FIXED ✅)
**Error:** Malformed query with single quotes (ex: "60's")
**File:** `backend/app/drive/manager.py` (methods `upload_video`, `ensure_folder`)
**Fix:**
```python
escaped_name = name.replace("'", "\\'")
query = f"name='{escaped_name}' and '{parent_id}' in parents and trashed=false"
```

---

## 💡 Code Patterns

### Backend (Python) - Modular Architecture

#### Router Pattern (router.py)
```python
from fastapi import APIRouter, Request
from .service import business_logic
from .schemas import RequestModel, ResponseModel
from app.core.logging import get_module_logger
from app.core.errors import raise_error, ErrorCode
from app.core.rate_limit import limiter, RateLimits

logger = get_module_logger("module")
router = APIRouter(prefix="/api/module", tags=["module"])

@router.post("/endpoint")
@limiter.limit(RateLimits.DEFAULT)
async def endpoint_name(request: Request, body: RequestModel) -> ResponseModel:
    """Descrição do endpoint (aparece em /docs)"""
    try:
        result = business_logic(body)
        logger.info(f"Processed request successfully")
        return ResponseModel(data=result)
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise_error(400, ErrorCode.VALIDATION_ERROR, str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise_error(500, ErrorCode.INTERNAL_ERROR, "Internal server error")
```

#### Service Pattern (service.py)
```python
from .schemas import RequestModel

def business_logic(request: RequestModel) -> dict:
    """Lógica de negócio isolada do router"""
    # Processar request
    return {"status": "success"}
```

#### Streaming Response
```python
def iterfile():
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            yield chunk

return StreamingResponse(
    iterfile(),
    media_type="video/mp4",
    headers={
        "Accept-Ranges": "bytes",
        "Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}"
    }
)
```

### Frontend (TypeScript/React)

#### Component Pattern (Client)
```typescript
"use client";

import { useState, useEffect } from "react";

export default function ComponentName() {
  const [state, setState] = useState<Type>(initialValue);

  useEffect(() => {
    // Side effects
  }, [dependencies]);

  const handleAction = async () => {
    try {
      const response = await fetch("/api/endpoint");
      const data = await response.json();
      setState(data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div className="tailwind-classes">
      {/* JSX */}
    </div>
  );
}
```

#### Component Pattern (Server)
```typescript
import { fetchLocalVideosPage } from "@/lib/server/api";

export default async function LibraryPage() {
  const data = await fetchLocalVideosPage(1, 12);
  return <ClientGrid initialData={data.videos} />;
}
```

#### API call pattern (client via Next BFF)
```typescript
import { deleteLocalVideo } from "@/lib/client/api";

await deleteLocalVideo("Channel/Video.mp4");
```

#### API call pattern (Route Handler + revalidation)
```typescript
import { proxyJsonWithRevalidate } from "@/lib/server/route-utils";
import { CACHE_TAG_SETS } from "@/lib/server/tags";

export async function POST(request: Request) {
  return proxyJsonWithRevalidate(
    "http://localhost:8000/api/endpoint",
    { method: "POST", body: await request.text() },
    CACHE_TAG_SETS.LOCAL_MUTATION
  );
}
```

---

## 🚨 Critical Attention Points

### Python
1. **ALWAYS escape `'` in Drive:** `name.replace("'", "\\'")` queries
2. **ALWAYS use RFC 5987 in headers:** `filename*=UTF-8''{quote(name)}`
3. **ALWAYS enable venv:** Use `./run.sh`, not `python app/main.py`
4. **Blocking IO must exit the event loop:** use `core/blocking.py` (to_thread)
5. **Jobs are in-memory:** multiple workers require shared storage (Redis/DB)
6. **ALWAYS try/except with traceback on endpoints**
7. **ALWAYS follow the modular pattern:** router.py → service.py → schemas.py

### TypeScript
1. **ALWAYS use `"use client"` in interactive components**
2. **ALWAYS use absolute paths:** `/api/videos` not `api/videos`
3. **ALWAYS import CSS from Vidstack into the layout:**
- `import "@vidstack/react/player/styles/default/theme.css";`
- `import "@vidstack/react/player/styles/default/layouts/video.css";`
4. **ALWAYS type variables:** Avoid `any`

---

## 🔐 Environment and Configuration Variables

### Backend (.env)
```bash
# Copiar .env.example para .env e ajustar conforme necessário
cp backend/.env.example backend/.env

# Variáveis disponíveis:
APP_NAME=YT-Archiver API          # Nome da aplicação
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=pretty                  # pretty, text, json
LOG_COLOR=true                     # cores nos logs (pretty/text)
HOST=0.0.0.0                       # Host do servidor
PORT=8000                          # Porta do servidor
METRICS_ENABLED=true               # Expor /metrics
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
DOWNLOADS_DIR=./downloads          # Diretório de downloads
DEFAULT_MAX_RESOLUTION=1080        # Resolução padrão
JOB_EXPIRY_HOURS=24               # Tempo para limpeza de jobs
JOB_STORE_BACKEND=memory           # memory | redis
REDIS_URL=redis://localhost:6379/0 # Usado quando JOB_STORE_BACKEND=redis
CATALOG_ENABLED=false              # Catálogo SQLite (local + drive)
CATALOG_DB_PATH=database.db        # Catalog path
CATALOG_DRIVE_AUTO_PUBLISH=true    # Publica snapshot após mutações do Drive
CATALOG_DRIVE_REQUIRE_IMPORT_BEFORE_PUBLISH=true  # Proteção contra overwrite
CATALOG_DRIVE_ALLOW_LEGACY_LISTING_FALLBACK=false # Fallback to direct listing
BLOCKING_DRIVE_CONCURRENCY=3       # Limite de IO bloqueante (Drive)
BLOCKING_FS_CONCURRENCY=2          # Limite de IO bloqueante (filesystem)
BLOCKING_CATALOG_CONCURRENCY=4     # Limite de IO bloqueante (catalog)
DRIVE_CACHE_ENABLED=true           # Cache SQLite do Drive
DRIVE_CACHE_DB_PATH=drive_cache.db # Caminho do cache do Drive
DRIVE_CACHE_SYNC_INTERVAL=30       # Minutos entre syncs
DRIVE_CACHE_FALLBACK_TO_API=true   # Fallback para API quando cache falhar
DRIVE_UPLOAD_CHUNK_SIZE=8388608    # Chunk size para upload resumable

# For the complete list of variables, see `backend/app/config.py`.

# Configuration files:
backend/credentials.json    # OAuth Google (obter no Cloud Console)
backend/token.json          # Gerado automaticamente após auth
backend/archive.txt         # Gerado automaticamente
backend/database.db         # Catálogo SQLite (local + drive)
backend/drive_cache.db      # Cache SQLite do Drive (opcional)
```

### Frontend
```bash
# Next.js usa variáveis de ambiente
# Arquivo: frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🛠️ Development Commands

### Initial Setup
```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Development
```bash
# Backend (uvicorn com hot reload)
cd backend && ./run.sh
# Ou manualmente:
# source .venv/bin/activate && uvicorn app.main:app --reload

# API + worker (recomendado para prod ou simulação)
# WORKER_ROLE=api ./run.sh
# WORKER_ROLE=worker PORT=8001 ./run.sh

# Frontend
cd frontend && npm run dev

# Ambos (script automático)
./start-dev.sh
```

### Tests
```bash
# Backend - Testes automatizados (pytest) - 63 testes (sem drive_cache)
cd backend && source .venv/bin/activate
python -m pytest -q -k "not drive_cache"
python -m pytest tests/ --cov=app --cov-report=html -k "not drive_cache"
python -m pytest tests/test_validators.py -v  # Single file

# Frontend - Lint e Build
cd frontend
npm run lint                        # ESLint (0 errors, ~7 warnings)
npm run build                       # Build de produção
npx tsc --noEmit                    # TypeScript check

# Test endpoints manualmente
curl http://localhost:8000/
curl http://localhost:8000/api/videos
curl http://localhost:8000/api/drive/auth-status

# Ver logs
# Backend: terminal onde rodou ./run.sh
# Frontend: console do navegador (F12)
```

### Debugging
```bash
# Matar processos travados
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend

# Reiniciar backend
cd backend && ./run.sh

# Build de produção frontend
cd frontend && npm run build && npm start
```

---

## 📊 Data Model

### DownloadRequest (API)
```python
{
  "url": str,                      # REQUIRED
  "download_type": "single" | "playlist",
  "max_res": int | None,           # Ex: 1080
  "subs": bool,
  "audio_only": bool,
  "path": str | None,              # Ex: "Curso/Modulo 01"
  "file_name": str | None,         # Ex: "Aula 01"
  "referer": str | None,
  "origin": str | None,
  "cookies_file": str | None,
  "archive_id": str | None,
  "delay_between_downloads": int,  # Segundos
  "batch_size": int,
  "delay_between_batches": int,
  "randomize_delay": bool
}
```

Notes (Download):
- Output directory is fixed (`DOWNLOADS_DIR`).
- Naming: `Uploader/Playlist/Titulo.ext` (without date/ID).
- If the file already exists, the download fails and does not overwrite.

### Job (Response)
```python
{
  "id": str,                       # UUID
  "status": "pending" | "running" | "completed" | "failed" | "cancelled",
  "progress": int,                 # 0-100
  "message": str,
  "started_at": str | None,        # ISO datetime
  "completed_at": str | None
}
```

### Video (Local)
```python
{
  "name": str,
  "path": str,                     # Caminho relativo
  "size": int,                     # Bytes
  "created_at": str,               # ISO datetime
  "thumbnail": str | None          # Path relativo
}
```

### Video (Drive)
```python
{
  "id": str,                       # File ID do Drive
  "name": str,
  "path": str,                     # Caminho completo
  "size": int,
  "created_at": str,
  "modified_at": str,
  "thumbnail": str | None          # thumbnailLink
}
```

---

## 🎯 Problem Solving Matrix

| Symptom | Probable Cause | Solution |
|---------|----------------|---------|
| 500 when streaming local | UnicodeEncodeError | ✅ Fixed in `app/library/router.py` |
| 500 when uploading Drive | Unescaped quotation marks | ✅ Fixed in `app/drive/manager.py` |
| ModuleNotFoundError | venv not activated | Use `./run.sh` |
| Import error in uvicorn | Wrong folder structure | Check `backend/app/` exists |
| Address in use (8000) | Backend crashed | `lsof -ti:8000 \| xargs kill -9` |
| Frontend does not connect | Backend not running | `cd backend && ./run.sh` |
| No video formats found | DRM or invalid URL | Check URL, try cookies |
| Upload Drive fails | missing credentials.json | See GOOGLE-DRIVE-SETUP.md |
| Player does not load | Vidstack CSS missing | Import styles in layout.tsx |
| Videos do not appear | Still downloading | Wait for job to complete |

---

## 📚 Useful Links

- **Project Documentation:** `README.md`
- **Guide for Claude:** `CLAUDE.md`
- **Bug Tracking:** `BUGS.md`
- **Setup Google Drive:** `GOOGLE-DRIVE-SETUP.md`
- **Interactive API:** http://localhost:8000/docs
- **yt-dlp Docs:** https://github.com/yt-dlp/yt-dlp
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Next.js 15 Docs:** https://nextjs.org/docs
- **shadcn/ui:** https://ui.shadcn.com/

---

**This document is a quick reference. For full details, see the main documentation files.**


## Observability

- /metrics (Prometheus) when METRICS_ENABLED=true
- /api/health for detailed status
- Local stack (Prometheus + Grafana): `docker compose -f docker-compose.observability.yml up -d`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Dashboards: `ops/observability/grafana/dashboards/`
- Alerts: `ops/observability/alerts.yml`
- Complete guide: `docs/project/OBSERVABILITY.md`

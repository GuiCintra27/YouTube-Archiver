# Referência Técnica Rápida - YT-Archiver

Guia de consulta rápida para desenvolvimento e troubleshooting.

**Última atualização:** 2025-11-29

---

## 🏗️ Arquitetura em Uma Olhada

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

## 🔧 Stack Técnico Completo

### Backend
| Componente | Tecnologia | Versão | Uso |
|------------|-----------|---------|-----|
| Framework | FastAPI | Latest | REST API |
| Server | Uvicorn | Latest | ASGI server |
| Validação | Pydantic | Latest | Request/response models |
| Download | yt-dlp | Latest | Video downloader |
| OAuth | google-auth-oauthlib | Latest | Google Drive auth |
| Drive API | google-api-python-client | Latest | Drive operations |
| Catalog DB | SQLite | Built-in | Catálogo persistente (local + drive) |
| Runtime | Python | 3.12+ | Backend runtime |

### Frontend
| Componente | Tecnologia | Versão | Uso |
|------------|-----------|---------|-----|
| Framework | Next.js | 15.0.0 | React framework |
| UI Library | shadcn/ui | Latest | Component library |
| CSS | Tailwind CSS | 3.4+ | Styling |
| Video Player | Plyr | 3.8.3 | HTML5 player |
| Icons | Lucide React | Latest | Icon system |
| Linter | ESLint | 9.x | Flat config |
| Runtime | Node.js | 18+ | Frontend runtime |

---

## 📁 Mapa de Arquivos Críticos

### Backend (Python) - Arquitetura Modular

```
backend/app/
├── main.py                         # ⭐ Entry point FastAPI
│   └── Registra todos os routers
│
├── config.py                       # Configurações globais (Settings)
│
├── core/                           # Módulo central compartilhado
│   ├── logging.py                  # ⭐ Sistema de logging estruturado
│   ├── blocking.py                 # ⭐ Offload de IO bloqueante (to_thread)
│   ├── validators.py               # ⭐ Validação de URLs, paths, filenames
│   ├── errors.py                   # ⭐ ErrorCode, AppException, raise_error()
│   ├── rate_limit.py               # Rate limiting com slowapi
│   ├── constants.py                # Constantes (MIME types, extensions)
│   ├── types.py                    # TypedDicts e type aliases
│   ├── exceptions.py               # HTTPExceptions customizadas (legacy)
│   └── security.py                 # Validações de path, sanitização (legacy)
│
├── catalog/                        # Catálogo persistente (SQLite)
│   ├── router.py                   # Endpoints /api/catalog/*
│   ├── service.py                  # Regras de catálogo
│   ├── repository.py               # Acesso ao SQLite
│   ├── database.py                 # Schema e conexões
│   └── drive_snapshot.py           # Snapshot drive (catalog-drive.json.gz)
│
├── downloads/                      # Módulo de downloads
│   ├── router.py                   # Endpoints /api/download, /api/video-info
│   ├── service.py                  # Lógica de negócio
│   ├── schemas.py                  # ⭐ DownloadRequest (Pydantic)
│   └── downloader.py               # ⭐ Engine yt-dlp wrapper
│       ├── Settings (dataclass):   Configurações de download
│       ├── Downloader.download():  Método principal
│       └── _base_opts():           Opções do yt-dlp
│
├── jobs/                           # Módulo de jobs assíncronos
│   ├── router.py                   # Endpoints /api/jobs/*
│   ├── service.py                  # Gerenciamento de jobs
│   ├── schemas.py                  # Modelos de jobs
│   ├── store.py                    # Storage in-memory (jobs_db)
│   └── cleanup.py                  # ⭐ Limpeza automática de jobs antigos
│
├── library/                        # Módulo de biblioteca local
│   ├── router.py                   # ⭐ Endpoints /api/videos/* (streaming)
│   ├── service.py                  # Scan de diretórios
│   ├── schemas.py                  # Modelos de vídeos
│   └── cache.py                    # ⭐ Cache de scan de diretórios (TTL 30s)
│
├── recordings/                     # Módulo de gravações
│   ├── router.py                   # Endpoint /api/recordings/upload
│   └── service.py                  # Salvamento de gravações
│
└── drive/                          # Módulo Google Drive
    ├── router.py                   # Endpoints /api/drive/*
    ├── service.py                  # Lógica de negócio
    ├── schemas.py                  # Modelos do Drive
    └── manager.py                  # ⭐ DriveManager
        ├── get_auth_url():         Gera URL OAuth
        ├── exchange_code():        Troca código por token
        ├── upload_video():         Upload com metadata
        ├── list_videos():          Lista recursiva
        └── ensure_folder():        Cria/obtém pastas

backend/
├── tests/                          # ⭐ Testes automatizados (pytest)
│   ├── conftest.py                 # Fixtures compartilhadas
│   ├── test_cache.py               # Testes do cache (7 testes)
│   ├── test_health.py              # Testes do health check (2 testes)
│   ├── test_jobs.py                # Testes de jobs (8 testes)
│   ├── test_library.py             # Testes da biblioteca (13 testes)
│   └── test_validators.py          # Testes de validação (16 testes)
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
│   │   ├── page.tsx                    # ⭐ Página principal (downloads)
│   │   ├── drive/page.tsx              # ⭐ Página Google Drive
│   │   ├── library/page.tsx            # Biblioteca de vídeos
│   │   ├── record/page.tsx             # Gravação de tela
│   │   ├── layout.tsx                  # ⭐ Layout global
│   │   └── globals.css                 # Estilos Tailwind
│   │
│   ├── components/
│   │   ├── common/                     # Componentes compartilhados
│   │   │   ├── error-boundary.tsx      # ⭐ Error Boundary com retry
│   │   │   ├── navigation.tsx          # Menu de navegação
│   │   │   ├── theme-provider.tsx      # Tema dark/light
│   │   │   ├── pagination.tsx          # Controles de paginação
│   │   │   └── videos/                 # VideoCard, VideoPlayer
│   │   ├── drive/                      # Componentes Google Drive
│   │   │   ├── drive-auth.tsx
│   │   │   ├── drive-video-grid.tsx
│   │   │   ├── drive-video-player.tsx
│   │   │   └── sync-panel.tsx
│   │   ├── home/                       # Componentes da Home
│   │   │   └── download-form.tsx       # ⭐ Formulário de download
│   │   ├── library/                    # Componentes da Biblioteca
│   │   │   └── paginated-video-grid.tsx
│   │   ├── record/                     # Gravação de tela
│   │   │   └── screen-recorder.tsx
│   │   └── ui/                         # shadcn/ui (30+ componentes)
│   │
│   ├── hooks/                          # ⭐ Hooks customizados
│   │   ├── index.ts                    # Barrel export
│   │   ├── use-api-url.ts              # ⭐ URL da API (SSR-safe)
│   │   └── use-fetch.ts                # Fetch com AbortController
│   │
│   └── lib/
│       ├── api-config.ts               # ⭐ Configuração da API
│       ├── api-client.ts               # Cliente HTTP tipado
│       ├── api-urls.ts                 # Constantes de endpoints
│       ├── url-validator.ts            # Validação de URLs
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

### Health & Info
```bash
GET  /                              # Health check
GET  /docs                          # API docs (Swagger)
```

### Downloads
```bash
POST /api/download                  # Inicia download
GET  /api/jobs                      # Lista jobs
GET  /api/jobs/{id}                 # Status do job
POST /api/jobs/{id}/cancel          # Cancela job
DELETE /api/jobs/{id}               # Remove job
POST /api/video-info                # Info sem baixar
```

### Biblioteca Local
```bash
GET  /api/videos                    # Lista vídeos
GET  /api/videos/stream/{path}      # Stream (206)
GET  /api/videos/thumbnail/{path}   # Thumbnail
DELETE /api/videos/{path}           # Exclui vídeo
```

### Catálogo (SQLite)
```bash
GET  /api/catalog/status            # Status do catálogo
POST /api/catalog/bootstrap-local   # Indexa vídeos locais
POST /api/catalog/drive/import      # Importa snapshot do Drive
POST /api/catalog/drive/publish     # Publica snapshot no Drive
POST /api/catalog/drive/rebuild     # Reconstrói catálogo lendo o Drive
```

### Google Drive
```bash
GET  /api/drive/auth-status         # Verifica auth
GET  /api/drive/auth-url            # URL OAuth
GET  /api/drive/oauth2callback      # Callback OAuth
GET  /api/drive/videos              # Lista vídeos
POST /api/drive/upload/{path}       # Upload individual
POST /api/drive/sync-all            # Upload em lote
GET  /api/drive/sync-status         # Status sync
GET  /api/drive/sync-items          # Itens paginados (diff)
GET  /api/drive/stream/{id}         # Stream (206)
GET  /api/drive/thumbnail/{id}      # Thumbnail
DELETE /api/drive/videos/{id}       # Remove vídeo + relacionados (retorna cleanup_job_id)
POST /api/drive/download            # Download (Drive -> local)
POST /api/drive/download-all        # Download em lote (Drive -> local)
```

---

## 🐛 Bugs Corrigidos (Reference Sheet)

### BUG #1: Local Video Streaming (CORRIGIDO ✅)
**Erro:** `UnicodeEncodeError: 'latin-1' codec can't encode character '\u29f8'`
**Arquivo:** `backend/app/library/router.py` (função `stream_video`)
**Fix:**
```python
from urllib.parse import quote
encoded_filename = quote(full_path.name)
headers = {
    "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
}
```

### BUG #2: Drive Upload (CORRIGIDO ✅)
**Erro:** Query malformada com aspas simples (ex: "60's")
**Arquivo:** `backend/app/drive/manager.py` (métodos `upload_video`, `ensure_folder`)
**Fix:**
```python
escaped_name = name.replace("'", "\\'")
query = f"name='{escaped_name}' and '{parent_id}' in parents and trashed=false"
```

---

## 💡 Padrões de Código

### Backend (Python) - Arquitetura Modular

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

#### Component Pattern
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

#### API Call Pattern
```typescript
const response = await fetch("http://localhost:8000/api/endpoint", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(data),
});

if (!response.ok) {
  throw new Error(`HTTP ${response.status}`);
}

const result = await response.json();
```

---

## 🚨 Gotchas Críticos

### Python
1. **SEMPRE escapar `'` em queries Drive:** `name.replace("'", "\\'")`
2. **SEMPRE usar RFC 5987 em headers:** `filename*=UTF-8''{quote(name)}`
3. **SEMPRE ativar venv:** Use `./run.sh`, não `python app/main.py`
4. **IO bloqueante deve sair do event loop:** use `core/blocking.py` (to_thread)
5. **Jobs são in-memory:** múltiplos workers exigem storage compartilhado (Redis/DB)
6. **SEMPRE try/except com traceback em endpoints**
7. **SEMPRE seguir o padrão modular:** router.py → service.py → schemas.py

### TypeScript
1. **SEMPRE usar `"use client"` em componentes interativos**
2. **SEMPRE usar paths absolutos:** `/api/videos` não `api/videos`
3. **SEMPRE importar Plyr CSS em layout:** `import "plyr-react/plyr.css"`
4. **SEMPRE tipar variáveis:** Evitar `any`

---

## 🔐 Variáveis de Ambiente e Configuração

### Backend (.env)
```bash
# Copiar .env.example para .env e ajustar conforme necessário
cp backend/.env.example backend/.env

# Variáveis disponíveis:
APP_NAME=YT-Archiver API          # Nome da aplicação
LOG_LEVEL=INFO                     # DEBUG, INFO, WARNING, ERROR
HOST=0.0.0.0                       # Host do servidor
PORT=8000                          # Porta do servidor
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
DOWNLOADS_DIR=./downloads          # Diretório de downloads
DEFAULT_MAX_RESOLUTION=1080        # Resolução padrão
JOB_EXPIRY_HOURS=24               # Tempo para limpeza de jobs
CATALOG_ENABLED=false              # Catálogo SQLite (local + drive)
CATALOG_DB_PATH=database.db        # Caminho do catálogo
CATALOG_DRIVE_AUTO_PUBLISH=true    # Publica snapshot após mutações do Drive
CATALOG_DRIVE_REQUIRE_IMPORT_BEFORE_PUBLISH=true  # Proteção contra overwrite
CATALOG_DRIVE_ALLOW_LEGACY_LISTING_FALLBACK=false # Fallback para listagem direta
BLOCKING_DRIVE_CONCURRENCY=3       # Limite de IO bloqueante (Drive)
BLOCKING_FS_CONCURRENCY=2          # Limite de IO bloqueante (filesystem)
BLOCKING_CATALOG_CONCURRENCY=4     # Limite de IO bloqueante (catalog)

# Arquivos de configuração:
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

## 🛠️ Comandos de Desenvolvimento

### Setup Inicial
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

### Desenvolvimento
```bash
# Backend (uvicorn com hot reload)
cd backend && ./run.sh
# Ou manualmente:
# source .venv/bin/activate && uvicorn app.main:app --reload

# Frontend
cd frontend && npm run dev

# Ambos (script automático)
./start-dev.sh
```

### Testing
```bash
# Backend - Testes automatizados (pytest) - 63 testes (sem drive_cache)
cd backend && source .venv/bin/activate
python -m pytest -q -k "not drive_cache"
python -m pytest tests/ --cov=app --cov-report=html -k "not drive_cache"
python -m pytest tests/test_validators.py -v  # Apenas um arquivo

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

## 📊 Modelo de Dados

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

## 🎯 Troubleshooting Matrix

| Sintoma | Causa Provável | Solução |
|---------|----------------|---------|
| 500 ao fazer stream local | UnicodeEncodeError | ✅ Corrigido em `app/library/router.py` |
| 500 ao fazer upload Drive | Aspas não escapadas | ✅ Corrigido em `app/drive/manager.py` |
| ModuleNotFoundError | venv não ativado | Use `./run.sh` |
| Import error no uvicorn | Estrutura de pasta errada | Verifique `backend/app/` existe |
| Address in use (8000) | Backend travado | `lsof -ti:8000 \| xargs kill -9` |
| Frontend não conecta | Backend não rodando | `cd backend && ./run.sh` |
| No video formats found | DRM ou URL inválida | Verificar URL, tentar cookies |
| Upload Drive falha | credentials.json faltando | Ver GOOGLE-DRIVE-SETUP.md |
| Player não carrega | Plyr CSS não importado | Importar em layout.tsx |
| Vídeos não aparecem | Ainda baixando | Aguardar job completar |

---

## 📚 Links Úteis

- **Documentação do Projeto:** `README.md`
- **Guia para Claude:** `CLAUDE.md`
- **Bug Tracking:** `BUGS.md`
- **Setup Google Drive:** `GOOGLE-DRIVE-SETUP.md`
- **API Interativa:** http://localhost:8000/docs
- **yt-dlp Docs:** https://github.com/yt-dlp/yt-dlp
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Next.js 15 Docs:** https://nextjs.org/docs
- **shadcn/ui:** https://ui.shadcn.com/

---

**Este documento é uma referência rápida. Para detalhes completos, consulte os arquivos de documentação principais.**

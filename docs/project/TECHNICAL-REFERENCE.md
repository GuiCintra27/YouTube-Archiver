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
| Runtime | Python | 3.12+ | Backend runtime |

### Frontend
| Componente | Tecnologia | Versão | Uso |
|------------|-----------|---------|-----|
| Framework | Next.js | 15.0.0 | React framework |
| UI Library | shadcn/ui | Latest | Component library |
| CSS | Tailwind CSS | 3.4+ | Styling |
| Video Player | Plyr | 3.8.3 | HTML5 player |
| Icons | Lucide React | Latest | Icon system |
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
│   ├── exceptions.py               # HTTPExceptions customizadas
│   └── security.py                 # Validações de path, sanitização
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
│   └── store.py                    # Storage in-memory (jobs_db)
│
├── library/                        # Módulo de biblioteca local
│   ├── router.py                   # ⭐ Endpoints /api/videos/* (streaming)
│   ├── service.py                  # Scan de diretórios
│   └── schemas.py                  # Modelos de vídeos
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
├── requirements.txt                # Dependências Python
├── run.sh                          # ⭐ Script de inicialização
└── credentials.json.example        # Template de credenciais
```

### Frontend (TypeScript/React)

```
frontend/src/
├── app/
│   ├── page.tsx                    # ⭐ Página principal
│   │   └── Componentes: DownloadForm, VideoGrid
│   │
│   ├── drive/page.tsx              # ⭐ Página Google Drive
│   │   └── Componentes: DriveAuth, DriveVideoGrid, SyncPanel
│   │
│   ├── layout.tsx                  # ⭐ Layout global
│   │   └── Imports: Plyr CSS, Navigation
│   │
│   └── globals.css                 # Estilos Tailwind
│
├── components/
│   ├── download-form.tsx           # Formulário de download (500+ linhas)
│   ├── video-grid.tsx              # Grid + player local (400+ linhas)
│   ├── drive-video-grid.tsx        # Grid de vídeos do Drive
│   ├── drive-video-player.tsx      # Player de vídeos do Drive
│   ├── sync-panel.tsx              # Painel de sincronização
│   ├── navigation.tsx              # Menu de navegação
│   └── ui/                         # Componentes shadcn/ui
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       └── ... (30+ componentes)
│
└── lib/
    ├── utils.ts                    # cn(), helpers
    └── url-validator.ts            # Validação de URLs YouTube
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

### Google Drive
```bash
GET  /api/drive/auth-status         # Verifica auth
GET  /api/drive/auth-url            # URL OAuth
GET  /api/drive/oauth2callback      # Callback OAuth
GET  /api/drive/videos              # Lista vídeos
POST /api/drive/upload/{path}       # Upload individual
POST /api/drive/sync-all            # Upload em lote
GET  /api/drive/sync-status         # Status sync
GET  /api/drive/stream/{id}         # Stream (206)
GET  /api/drive/thumbnail/{id}      # Thumbnail
DELETE /api/drive/videos/{id}       # Remove vídeo
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
from fastapi import APIRouter, HTTPException
from .service import business_logic
from .schemas import RequestModel, ResponseModel

router = APIRouter(prefix="/api/module", tags=["module"])

@router.post("/endpoint")
async def endpoint_name(request: RequestModel) -> ResponseModel:
    """Descrição do endpoint (aparece em /docs)"""
    try:
        result = business_logic(request)
        return ResponseModel(data=result)
    except Exception as e:
        import traceback
        print(f"[ERROR] {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
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
4. **SEMPRE try/except com traceback em endpoints**
5. **SEMPRE seguir o padrão modular:** router.py → service.py → schemas.py

### TypeScript
1. **SEMPRE usar `"use client"` em componentes interativos**
2. **SEMPRE usar paths absolutos:** `/api/videos` não `api/videos`
3. **SEMPRE importar Plyr CSS em layout:** `import "plyr-react/plyr.css"`
4. **SEMPRE tipar variáveis:** Evitar `any`

---

## 🔐 Variáveis de Ambiente e Configuração

### Backend
```bash
# Nenhuma variável de ambiente necessária
# Configuração via arquivos:
backend/credentials.json    # OAuth Google (obter no Cloud Console)
backend/token.json          # Gerado automaticamente após auth
backend/archive.txt         # Gerado automaticamente
```

### Frontend
```bash
# Next.js usa variáveis de ambiente
# Nenhuma configuração necessária por padrão
# Backend hardcoded em http://localhost:8000
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
# Test endpoints
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

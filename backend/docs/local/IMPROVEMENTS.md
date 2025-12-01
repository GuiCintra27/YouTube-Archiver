# Backend Improvements Roadmap

**Data de Criação:** 2025-11-29
**Última Atualização:** 2025-11-30
**Arquitetura Atual:** FastAPI modular (NestJS-like)

Este documento lista melhorias identificadas para o backend do YT-Archiver, organizadas por prioridade e categoria.

---

## Status das Implementações

| # | Melhoria | Status | Commit |
|---|----------|--------|--------|
| 1 | Sistema de Logging Estruturado | ✅ Implementado | `32bd81f` |
| 2 | Validação de Input Robusta | ✅ Implementado | `05c65e4` |
| 3 | Variáveis de Ambiente com pydantic-settings | ✅ Implementado | `b999a6c` |
| 4 | Limpeza Automática de Jobs | ✅ Implementado | `a76c959` |
| 5 | Respostas de Erro Padronizadas | ✅ Implementado | `9face73` |
| 6 | Rate Limiting com slowapi | ✅ Implementado | `6db3165` |
| 7 | Cache de Scan de Diretórios | ✅ Implementado | `eb51dcd` |
| 8 | Documentação de API (Swagger) | ✅ Implementado | `bf2f92b` |
| 9 | Testes Automatizados | ✅ Implementado | `0e3ca51` |
| 10 | Constantes Centralizadas | ✅ Implementado | `e0fbcf6` |
| 11 | Type Hints Completas | ✅ Implementado | `1a2ac4b` |
| 12 | Fila Assíncrona de Upload com Processamento Paralelo | ✅ Implementado | `35ca3c5` |
| 13 | Cache em Memória para Drive API | ✅ Implementado | `6c87ed3` |
| 14 | Upload de Arquivos Externos para o Drive | ✅ Implementado | `6ab1e18` |
| 15 | Download do Drive para Local | ✅ Implementado | `dcf5e89` |

---

## Funcionalidades Recentes (v2.2+)

### 12. Fila Assíncrona de Upload com Processamento Paralelo

**Status:** ✅ Implementado
**Commit:** `35ca3c5`
**Impacto:** Alto (Performance)

**Implementação:**
- Sistema de fila assíncrona para uploads do Google Drive com `asyncio.Semaphore(3)`
- Endpoints retornam `job_id` imediatamente (não-bloqueante)
- Tasks de upload executam em background com `asyncio.create_task()`
- Uso de `asyncio.to_thread()` para operações de I/O bloqueantes
- Frontend faz polling em `/api/jobs/{id}` para progresso em tempo real

**Arquivos Modificados:**
- `app/drive/service.py` - Funções de upload assíncrono
- `app/drive/router.py` - Endpoints não-bloqueantes
- `app/jobs/store.py` - Storage de jobs

---

### 13. Cache em Memória para Drive API

**Status:** ✅ Implementado
**Commit:** `6c87ed3`
**Impacto:** Alto (Performance)

**Implementação:**
- Classe `DriveCache` com TTL de 60 segundos para listagem de vídeos
- Reduz chamadas repetidas à API de ~15s para ~10ms em requests cacheados
- Correção no carregamento de thumbnails usando URLs diretas do Google (evita erros ORB)
- Invalidação automática do cache após operações de upload/delete

**Arquivos Criados/Modificados:**
- `app/drive/manager.py` - Classe `DriveCache` e integração

---

### 14. Upload de Arquivos Externos para o Drive

**Status:** ✅ Implementado
**Commit:** `6ab1e18`
**Impacto:** Médio (Feature)

**Implementação:**
- Permite upload de qualquer vídeo do PC para o Google Drive
- Suporte para arquivos extras (thumbnails, legendas, transcrições)
- Método `upload_to_folder()` no DriveManager
- Função assíncrona `upload_external_files()` no serviço
- Endpoint `POST /api/drive/upload-external`
- Arquivos salvos em `/tmp` e limpos após upload
- Tracking de progresso via job polling

**Arquivos Modificados:**
- `app/drive/manager.py` - Método `upload_to_folder()`
- `app/drive/service.py` - Função `upload_external_files()`
- `app/drive/router.py` - Endpoint `/upload-external`

---

### 15. Download do Drive para Local

**Status:** ✅ Implementado
**Commit:** `dcf5e89`
**Impacto:** Alto (Feature)

**Implementação:**
- Download de vídeos do Google Drive para armazenamento local
- Sincronização bidirecional entre biblioteca local e Drive
- Método `download_file()` no DriveManager com callback de progresso
- Método `_download_related_files()` para baixar thumbnails, metadata, legendas
- Método `get_video_by_path()` para resolução path-to-ID
- Funções `download_single_from_drive()` e `download_all_from_drive()`
- Tipo de job `DRIVE_DOWNLOAD` para tracking de progresso
- Endpoints `POST /api/drive/download` e `POST /api/drive/download-all`
- Suporte a até 3 downloads simultâneos com `asyncio.Semaphore`
- Progresso em tempo real durante o download (atualizado a cada chunk de 8MB)

**Arquivos Modificados:**
- `app/drive/manager.py` - Métodos de download
- `app/drive/service.py` - Funções de serviço de download
- `app/drive/router.py` - Endpoints de download
- `app/jobs/store.py` - Tipo `DRIVE_DOWNLOAD`

---

## Prioridade Alta

### 1. Sistema de Logging Estruturado

**Status:** ✅ Implementado
**Impacto:** Alto
**Esforço:** Médio

**Problema Atual:**
- Uso de `print()` statements espalhados pelo código
- Sem níveis de log (DEBUG, INFO, WARNING, ERROR)
- Difícil rastrear problemas em produção

**Solução Proposta:**
```python
# backend/app/core/logging.py
import logging
import sys
from app.config import settings

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    return root_logger

logger = setup_logging()
```

**Arquivos a Modificar:**
- Criar: `backend/app/core/logging.py`
- Modificar: `backend/app/config.py` (adicionar LOG_LEVEL)
- Modificar: Todos os arquivos com `print()` statements

**Exemplo de Uso:**
```python
from app.core.logging import logger

# Substituir:
print(f"[DEBUG] Processing download: {url}")

# Por:
logger.debug(f"Processing download: {url}")
logger.info(f"Download started for: {url}")
logger.error(f"Failed to download: {url}", exc_info=True)
```

---

### 2. Validação de Input Robusta

**Status:** ✅ Implementado
**Impacto:** Alto (Segurança)
**Esforço:** Médio

**Problema Atual:**
- Validação básica de URLs
- Falta de sanitização em alguns inputs
- Path traversal potencial em alguns endpoints

**Solução Proposta:**

```python
# backend/app/core/validators.py
from pydantic import field_validator, HttpUrl
from urllib.parse import urlparse
import re

ALLOWED_DOMAINS = [
    'youtube.com', 'www.youtube.com', 'youtu.be',
    'm.youtube.com', 'music.youtube.com'
]

class URLValidator:
    @staticmethod
    def validate_youtube_url(url: str) -> str:
        """Valida se a URL é do YouTube."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if not any(domain == d or domain.endswith(f'.{d}') for d in ALLOWED_DOMAINS):
            raise ValueError(f"URL must be from YouTube. Got: {domain}")

        return url

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove caracteres perigosos de nomes de arquivo."""
        # Remove path traversal
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        # Remove caracteres especiais perigosos
        filename = re.sub(r'[<>:"|?*]', '', filename)
        return filename.strip()

class PathValidator:
    @staticmethod
    def validate_path_within_base(path: str, base_dir: Path) -> Path:
        """Garante que o path está dentro do diretório base."""
        full_path = (base_dir / path).resolve()

        if not str(full_path).startswith(str(base_dir.resolve())):
            raise ValueError("Path traversal detected")

        return full_path
```

**Arquivos a Modificar:**
- Criar: `backend/app/core/validators.py`
- Modificar: `backend/app/downloads/schemas.py`
- Modificar: `backend/app/library/router.py`
- Modificar: `backend/app/drive/router.py`

---

### 3. Variáveis de Ambiente com pydantic-settings

**Status:** ✅ Implementado
**Impacto:** Alto
**Esforço:** Baixo

**Problema Atual:**
- Valores hardcoded em `config.py`
- Difícil mudar configurações sem editar código
- Sem suporte a diferentes ambientes (dev/prod)

**Solução Proposta:**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "YT-Archiver"
    APP_VERSION: str = "2.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DOWNLOADS_DIR: Path = BASE_DIR / "downloads"

    # Google Drive
    DRIVE_CREDENTIALS_FILE: Path = BASE_DIR / "credentials.json"
    DRIVE_TOKEN_FILE: Path = BASE_DIR / "token.json"
    DRIVE_ROOT_FOLDER: str = "YT-Archiver"

    # Download Settings
    DEFAULT_MAX_RESOLUTION: int = 1080
    DEFAULT_DELAY_BETWEEN_DOWNLOADS: int = 2
    MAX_CONCURRENT_DOWNLOADS: int = 3

    # Job Settings
    JOB_EXPIRY_HOURS: int = 24
    JOB_CLEANUP_INTERVAL_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
```

**Criar arquivo `.env.example`:**
```env
# Application
APP_NAME=YT-Archiver
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000

# Downloads
DEFAULT_MAX_RESOLUTION=1080
MAX_CONCURRENT_DOWNLOADS=3

# Jobs
JOB_EXPIRY_HOURS=24
```

**Dependências:**
```bash
pip install pydantic-settings python-dotenv
```

---

### 4. Limpeza Automática de Jobs

**Status:** ✅ Implementado
**Impacto:** Alto (Memory)
**Esforço:** Baixo

**Problema Atual:**
- Jobs ficam em memória indefinidamente
- Sem cleanup de jobs antigos
- Potencial memory leak em uso prolongado

**Solução Proposta:**

```python
# backend/app/jobs/cleanup.py
import asyncio
from datetime import datetime, timedelta
from app.jobs.store import jobs_db
from app.config import settings
from app.core.logging import logger

async def cleanup_old_jobs():
    """Remove jobs com mais de X horas."""
    while True:
        try:
            cutoff = datetime.now() - timedelta(hours=settings.JOB_EXPIRY_HOURS)

            jobs_to_remove = []
            for job_id, job in jobs_db.items():
                if job.completed_at and job.completed_at < cutoff:
                    jobs_to_remove.append(job_id)

            for job_id in jobs_to_remove:
                del jobs_db[job_id]
                logger.info(f"Cleaned up old job: {job_id}")

            if jobs_to_remove:
                logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

        except Exception as e:
            logger.error(f"Error in job cleanup: {e}")

        # Aguardar intervalo configurado
        await asyncio.sleep(settings.JOB_CLEANUP_INTERVAL_MINUTES * 60)

# Iniciar no startup do app
# backend/app/main.py
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_jobs())
```

**Arquivos a Modificar:**
- Criar: `backend/app/jobs/cleanup.py`
- Modificar: `backend/app/main.py`
- Modificar: `backend/app/config.py`

---

### 5. Respostas de Erro Padronizadas

**Status:** ✅ Implementado
**Impacto:** Médio
**Esforço:** Baixo

**Problema Atual:**
- Mensagens de erro inconsistentes
- Falta de códigos de erro estruturados
- Difícil para o frontend interpretar erros

**Solução Proposta:**

```python
# backend/app/core/errors.py
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Any

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Any] = None

class AppError:
    """Códigos de erro padronizados."""

    # Downloads
    INVALID_URL = "INVALID_URL"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    VIDEO_NOT_FOUND = "VIDEO_NOT_FOUND"

    # Jobs
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    JOB_ALREADY_CANCELLED = "JOB_ALREADY_CANCELLED"

    # Drive
    DRIVE_NOT_AUTHENTICATED = "DRIVE_NOT_AUTHENTICATED"
    DRIVE_UPLOAD_FAILED = "DRIVE_UPLOAD_FAILED"
    DRIVE_FILE_NOT_FOUND = "DRIVE_FILE_NOT_FOUND"

    # Library
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"

def raise_error(
    status_code: int,
    error_code: str,
    message: str,
    details: Any = None
):
    """Levanta uma HTTPException padronizada."""
    raise HTTPException(
        status_code=status_code,
        detail=ErrorResponse(
            error_code=error_code,
            message=message,
            details=details
        ).model_dump()
    )
```

**Exemplo de Uso:**
```python
from app.core.errors import raise_error, AppError

# Substituir:
raise HTTPException(status_code=404, detail="Video not found")

# Por:
raise_error(404, AppError.VIDEO_NOT_FOUND, "Video not found", {"path": video_path})
```

---

## Prioridade Média

### 6. Rate Limiting com slowapi

**Status:** ✅ Implementado
**Impacto:** Médio (Segurança)
**Esforço:** Baixo

**Problema Atual:**
- Sem proteção contra abuso de API
- Endpoints podem ser sobrecarregados

**Solução Proposta:**

```python
# backend/app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# backend/app/main.py
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Uso nos routers:
from app.core.rate_limit import limiter

@router.post("/download")
@limiter.limit("10/minute")
async def start_download(request: Request, ...):
    ...
```

**Dependências:**
```bash
pip install slowapi
```

**Limites Sugeridos:**
- `/api/download`: 10/minute
- `/api/drive/upload`: 5/minute
- `/api/drive/sync-all`: 1/minute
- `/api/videos`: 30/minute

---

### 7. Cache de Scan de Diretórios

**Status:** ✅ Implementado
**Impacto:** Médio (Performance)
**Esforço:** Médio

**Problema Atual:**
- Scan de diretório a cada request de `/api/videos`
- Lento com muitos arquivos
- I/O desnecessário

**Solução Proposta:**

```python
# backend/app/library/cache.py
from datetime import datetime, timedelta
from typing import Optional, List
from app.library.schemas import VideoInfo
from app.config import settings

class VideoCache:
    def __init__(self, ttl_seconds: int = 30):
        self._cache: Optional[List[VideoInfo]] = None
        self._last_scan: Optional[datetime] = None
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self) -> Optional[List[VideoInfo]]:
        """Retorna cache se válido."""
        if self._cache is None or self._last_scan is None:
            return None

        if datetime.now() - self._last_scan > self._ttl:
            return None

        return self._cache

    def set(self, videos: List[VideoInfo]):
        """Atualiza o cache."""
        self._cache = videos
        self._last_scan = datetime.now()

    def invalidate(self):
        """Invalida o cache (após download ou exclusão)."""
        self._cache = None
        self._last_scan = None

video_cache = VideoCache(ttl_seconds=30)
```

**Uso:**
```python
# backend/app/library/service.py
from app.library.cache import video_cache

def list_videos() -> List[VideoInfo]:
    cached = video_cache.get()
    if cached is not None:
        return cached

    videos = scan_directory()
    video_cache.set(videos)
    return videos

# Invalidar após operações
def delete_video(path: str):
    # ... deletar arquivo ...
    video_cache.invalidate()
```

---

### 8. Documentação de API (Swagger)

**Status:** ✅ Implementado
**Impacto:** Médio
**Esforço:** Baixo

**Problema Atual:**
- Docstrings incompletas
- Exemplos de request/response faltando
- Descrições genéricas

**Solução Proposta:**

```python
# Melhorar docstrings e adicionar exemplos
@router.post(
    "/download",
    response_model=DownloadResponse,
    summary="Inicia download de vídeo",
    description="""
    Inicia o download de um vídeo ou playlist do YouTube.

    **Tipos de Download:**
    - `single`: Download de um único vídeo
    - `playlist`: Download de toda a playlist

    **Opções Avançadas:**
    - `max_res`: Resolução máxima (720, 1080, 1440, 2160)
    - `audio_only`: Extrai apenas o áudio em MP3
    - `subs`: Baixa legendas se disponíveis
    """,
    responses={
        200: {
            "description": "Download iniciado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "abc123",
                        "status": "pending",
                        "message": "Download queued"
                    }
                }
            }
        },
        400: {"description": "URL inválida"},
        500: {"description": "Erro interno"}
    }
)
async def start_download(request: DownloadRequest):
    ...
```

---

### 9. Testes Automatizados

**Status:** ✅ Implementado
**Impacto:** Alto
**Esforço:** Alto

**Estrutura Sugerida:**

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Fixtures compartilhadas
│   ├── test_downloads.py
│   ├── test_jobs.py
│   ├── test_library.py
│   ├── test_drive.py
│   └── test_integration.py
```

**Exemplo de Teste:**

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_downloads_dir(tmp_path):
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    return downloads

# backend/tests/test_library.py
def test_list_videos_empty(client, mock_downloads_dir, monkeypatch):
    monkeypatch.setattr("app.config.settings.DOWNLOADS_DIR", mock_downloads_dir)

    response = client.get("/api/videos")

    assert response.status_code == 200
    assert response.json() == []

def test_list_videos_with_files(client, mock_downloads_dir, monkeypatch):
    # Criar arquivo de teste
    (mock_downloads_dir / "test.mp4").write_bytes(b"fake video")
    monkeypatch.setattr("app.config.settings.DOWNLOADS_DIR", mock_downloads_dir)

    response = client.get("/api/videos")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "test.mp4"
```

**Dependências:**
```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

**Comandos:**
```bash
# Rodar todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Apenas um módulo
pytest tests/test_library.py -v
```

---

## Prioridade Baixa

### 10. Constantes Centralizadas

**Status:** ✅ Implementado
**Impacto:** Baixo
**Esforço:** Baixo

**Solução Proposta:**

```python
# backend/app/core/constants.py

# MIME Types
MIME_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".wav": "audio/wav",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

# File Extensions
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".avi", ".mov", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".flac", ".opus", ".ogg"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass", ".sub"}
METADATA_EXTENSIONS = {".json", ".info.json", ".description"}

# Related File Patterns
RELATED_FILE_SUFFIXES = [
    ".info.json",
    ".description",
    ".jpg",
    ".webp",
    ".png",
    ".srt",
    ".vtt",
]

# Job Status
class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Chunk Sizes
STREAM_CHUNK_SIZE = 8 * 1024  # 8KB
UPLOAD_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB
```

---

### 11. Type Hints Completas

**Status:** ✅ Implementado
**Impacto:** Baixo
**Esforço:** Médio

**Áreas a Melhorar:**

```python
# Exemplo de melhorias em downloader.py
from typing import Callable, Optional, Dict, Any, List
from pathlib import Path

ProgressCallback = Callable[[int, str], None]

class Downloader:
    def __init__(self, settings: Settings):
        self.settings: Settings = settings
        self._progress_callback: Optional[ProgressCallback] = None

    def download(
        self,
        url: str,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Dict[str, Any]:
        ...

    def _base_opts(self) -> Dict[str, Any]:
        ...
```

---

## Checklist de Implementação

### Fase 1 - Fundação (Semana 1-2)
- [ ] Implementar sistema de logging
- [ ] Configurar pydantic-settings
- [ ] Criar .env.example
- [ ] Adicionar validadores de input

### Fase 2 - Robustez (Semana 3-4)
- [ ] Implementar cleanup de jobs
- [ ] Padronizar respostas de erro
- [ ] Adicionar rate limiting

### Fase 3 - Performance (Semana 5-6)
- [ ] Implementar cache de diretórios
- [ ] Otimizar streaming de vídeos
- [ ] Revisar queries do Drive

### Fase 4 - Qualidade (Contínuo)
- [ ] Escrever testes unitários
- [ ] Melhorar documentação Swagger
- [ ] Adicionar type hints completas
- [ ] Centralizar constantes

---

## Notas Importantes

### Compatibilidade
- Todas as melhorias devem manter compatibilidade com o frontend existente
- APIs existentes não devem quebrar (adicionar, não modificar)
- Testar cada mudança com o frontend antes de fazer merge

### Priorização
- Prioridade Alta = Impacto em segurança, estabilidade ou experiência
- Prioridade Média = Melhorias importantes mas não urgentes
- Prioridade Baixa = Nice to have, refatorações

### Dependências a Adicionar
```bash
# Adicionar ao requirements.txt
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
slowapi>=0.1.9
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.24.0
```

---

**Última atualização:** 2025-11-30

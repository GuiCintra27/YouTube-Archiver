"""
Downloads router - API endpoints for video downloads.

Provides endpoints for:
- Getting video/playlist metadata without downloading
- Starting background download jobs
"""
from fastapi import APIRouter, HTTPException, Request

from .schemas import VideoInfoRequest, VideoInfoResponse, DownloadRequest, DownloadResponse
from .service import get_video_info, create_download_settings
from app.jobs.service import create_and_start_job
from app.core.rate_limit import limiter, RateLimits
from app.core.responses import job_response

router = APIRouter(prefix="/api", tags=["downloads"])


@router.post(
    "/video-info",
    response_model=VideoInfoResponse,
    summary="Obter informações do vídeo",
    description="""
Obtém metadados de um vídeo ou playlist do YouTube sem baixar.

**Informações retornadas:**
- Para vídeos: título, canal, duração, visualizações, thumbnail
- Para playlists: título, canal, quantidade de vídeos

**Uso típico:** Pré-visualização antes de iniciar download.
    """,
    responses={
        200: {"description": "Informações obtidas com sucesso"},
        400: {"description": "URL inválida ou vídeo não encontrado"},
    }
)
@limiter.limit(RateLimits.LIST_VIDEOS)
async def video_info(request: Request, body: VideoInfoRequest):
    """Obtém informações sobre um vídeo sem baixar."""
    try:
        info = await get_video_info(body.url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/download",
    response_model=DownloadResponse,
    summary="Iniciar download de vídeo",
    description="""
Inicia o download de um vídeo ou playlist do YouTube em background.

**Tipos de download suportados:**
- Vídeo individual
- Playlist completa
- Arquivo .txt com lista de URLs

**Fluxo:**
1. Envie a requisição com a URL e opções
2. Receba um `job_id` para acompanhamento
3. Consulte `/api/jobs/{job_id}` para ver o progresso
4. Use `/api/jobs/{job_id}/stream` para progresso em tempo real (SSE)

**Opções anti-ban:**
- `delay_between_downloads`: Pausa entre vídeos
- `batch_size` + `batch_delay`: Downloads em lotes
- `randomize_delay`: Variação aleatória nos delays
    """,
    responses={
        200: {"description": "Download iniciado com sucesso"},
        400: {"description": "URL inválida"},
        500: {"description": "Erro interno ao iniciar download"},
    }
)
@limiter.limit(RateLimits.DOWNLOAD_START)
async def start_download(request: Request, body: DownloadRequest):
    """Inicia um download em background."""
    try:
        job_id = await create_and_start_job(body)
        return job_response(job_id, "Download iniciado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

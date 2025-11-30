"""
Jobs router - API endpoints for job management.

Provides endpoints for:
- Listing all download jobs
- Getting individual job status
- Cancelling running jobs
- Deleting jobs from history
- Real-time progress streaming via SSE
"""
import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.rate_limit import limiter, RateLimits
from . import store
from .service import cancel_job
from app.core.exceptions import JobNotFoundException, InvalidRequestException

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get(
    "",
    summary="Listar todos os jobs",
    description="""
Lista todos os jobs de download registrados.

**Estados possíveis:**
- `pending`: Aguardando início
- `downloading`: Em progresso
- `completed`: Concluído com sucesso
- `error`: Falhou com erro
- `cancelled`: Cancelado pelo usuário

Os jobs são automaticamente removidos após 24 horas.
    """,
    responses={
        200: {
            "description": "Lista de jobs",
            "content": {
                "application/json": {
                    "example": {
                        "total": 2,
                        "jobs": [
                            {"id": "abc123", "status": "downloading", "progress": {"percent": 45.5}},
                            {"id": "def456", "status": "completed"}
                        ]
                    }
                }
            }
        }
    }
)
@limiter.limit(RateLimits.GET_STATUS)
async def list_jobs(request: Request):
    """Lista todos os jobs."""
    jobs = store.get_all_jobs()
    return {
        "total": len(jobs),
        "jobs": jobs,
    }


@router.get(
    "/{job_id}",
    summary="Obter status do job",
    description="""
Retorna o status atual de um job específico.

**Campos de progresso (quando downloading):**
- `percent`: Porcentagem concluída (0-100)
- `speed`: Velocidade de download
- `eta`: Tempo estimado restante
- `filename`: Nome do arquivo atual
    """,
    responses={
        200: {"description": "Detalhes do job"},
        404: {"description": "Job não encontrado"},
    }
)
@limiter.limit(RateLimits.GET_STATUS)
async def get_job_status(request: Request, job_id: str):
    """Obtém o status de um job."""
    job = store.get_job(job_id)
    if not job:
        raise JobNotFoundException()
    return job


@router.post(
    "/{job_id}/cancel",
    summary="Cancelar job",
    description="""
Cancela um job em execução.

Apenas jobs com status `pending` ou `downloading` podem ser cancelados.
Jobs já finalizados (`completed`, `error`, `cancelled`) não podem ser cancelados.
    """,
    responses={
        200: {"description": "Job cancelado com sucesso"},
        400: {"description": "Job não está em execução"},
        404: {"description": "Job não encontrado"},
    }
)
@limiter.limit(RateLimits.DELETE)
async def cancel_job_endpoint(request: Request, job_id: str):
    """Cancela um job em execução."""
    job = store.get_job(job_id)
    if not job:
        raise JobNotFoundException()

    # Only cancel running jobs
    if job["status"] not in ["pending", "downloading"]:
        raise InvalidRequestException("Job não está em execução")

    # Cancel task if exists
    task = store.get_task(job_id)
    if task:
        task.cancel()
        store.delete_task(job_id)

    # Mark as cancelled
    cancel_job(job_id)

    return {"status": "success", "message": "Download cancelado"}


@router.delete(
    "/{job_id}",
    summary="Remover job do histórico",
    description="""
Remove um job do histórico.

Se o job ainda estiver em execução, ele será cancelado primeiro.
Esta ação não pode ser desfeita.
    """,
    responses={
        200: {"description": "Job removido com sucesso"},
        404: {"description": "Job não encontrado"},
    }
)
@limiter.limit(RateLimits.DELETE)
async def delete_job(request: Request, job_id: str):
    """Remove um job do histórico."""
    if not store.job_exists(job_id):
        raise JobNotFoundException()

    # Cancel first if running
    task = store.get_task(job_id)
    if task:
        task.cancel()
        store.delete_task(job_id)

    store.delete_job(job_id)
    return {"status": "success", "message": "Job removido"}


@router.get(
    "/{job_id}/stream",
    summary="Stream de progresso (SSE)",
    description="""
Stream de progresso em tempo real usando Server-Sent Events (SSE).

**Conexão:**
- Use `EventSource` no JavaScript para conectar
- O stream envia atualizações a cada 500ms quando há mudanças
- O stream fecha automaticamente quando o job finaliza

**Exemplo JavaScript:**
```javascript
const eventSource = new EventSource('/api/jobs/abc123/stream');
eventSource.onmessage = (e) => {
    const job = JSON.parse(e.data);
    console.log(job.progress.percent);
};
```
    """,
    responses={
        200: {
            "description": "Stream SSE de eventos",
            "content": {"text/event-stream": {}}
        },
        404: {"description": "Job não encontrado"},
    }
)
@limiter.limit(RateLimits.GET_STATUS)
async def stream_job_progress(request: Request, job_id: str):
    """Stream de progresso em tempo real usando Server-Sent Events (SSE)."""
    if not store.job_exists(job_id):
        raise JobNotFoundException()

    async def event_generator():
        last_progress = None
        while True:
            job = store.get_job(job_id)
            if not job:
                break

            current_progress = job.get("progress", {})

            # Send update if changed
            if current_progress != last_progress:
                yield f"data: {json.dumps(job)}\n\n"
                last_progress = current_progress.copy() if current_progress else None

            # Stop if job finished
            if job["status"] in ["completed", "error", "cancelled"]:
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )

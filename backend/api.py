"""
API FastAPI para o YT-Archiver.
Fornece endpoints REST para download de vídeos com interface web.
"""
from __future__ import annotations
import os
import uuid
import asyncio
import shutil
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import asdict
from pathlib import Path
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from downloader import Settings, download_video, get_video_info

# Estado global para jobs
jobs_db: Dict[str, dict] = {}
active_tasks: Dict[str, asyncio.Task] = {}

app = FastAPI(
    title="YT-Archiver API",
    description="API para download de vídeos do YouTube e streams HLS",
    version="2.0.0",
)

# CORS para permitir frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Models ==========

class VideoInfoRequest(BaseModel):
    url: str = Field(..., description="URL do vídeo ou playlist")


class DownloadRequest(BaseModel):
    url: str = Field(..., description="URL do vídeo, playlist ou arquivo .txt")
    out_dir: str = Field(default="./downloads", description="Diretório de saída")
    archive_file: str = Field(default="./archive.txt", description="Arquivo de controle de downloads")
    fmt: str = Field(default="bv*+ba/b", description="Formato do vídeo")
    max_res: Optional[int] = Field(default=None, description="Resolução máxima (altura)")
    subs: bool = Field(default=True, description="Baixar legendas")
    auto_subs: bool = Field(default=True, description="Baixar legendas automáticas")
    sub_langs: str = Field(default="pt,en", description="Idiomas de legendas")
    thumbnails: bool = Field(default=True, description="Baixar miniaturas")
    audio_only: bool = Field(default=False, description="Apenas áudio (MP3)")
    limit: Optional[int] = Field(default=None, description="Limitar itens de playlist")
    cookies_file: Optional[str] = Field(default=None, description="Arquivo de cookies")
    referer: Optional[str] = Field(default=None, description="Header Referer")
    origin: Optional[str] = Field(default=None, description="Header Origin")
    user_agent: str = Field(default="yt-archiver", description="User Agent")
    concurrent_fragments: int = Field(default=10, description="Fragmentos simultâneos")
    path: Optional[str] = Field(default=None, description="Subpasta personalizada")
    file_name: Optional[str] = Field(default=None, description="Nome do arquivo")
    archive_id: Optional[str] = Field(default=None, description="ID customizado para archive")
    # Anti-ban / Rate limiting
    delay_between_downloads: int = Field(default=0, description="Segundos entre vídeos (anti-ban)")
    batch_size: Optional[int] = Field(default=None, description="Vídeos por batch (0=desabilitado)")
    batch_delay: int = Field(default=0, description="Segundos entre batches")
    randomize_delay: bool = Field(default=False, description="Randomizar delays")


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, downloading, completed, error
    created_at: str
    url: str
    progress: dict = {}
    result: Optional[dict] = None
    error: Optional[str] = None


# ========== Helper Functions ==========

def create_job(url: str, request: DownloadRequest) -> str:
    """Cria um novo job de download"""
    job_id = str(uuid.uuid4())
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "url": url,
        "request": request.model_dump(),
        "progress": {},
        "result": None,
        "error": None,
    }
    return job_id


def update_job_progress(job_id: str, progress: dict):
    """Atualiza o progresso de um job"""
    if job_id in jobs_db:
        jobs_db[job_id]["progress"] = progress
        if progress.get("status") == "downloading":
            jobs_db[job_id]["status"] = "downloading"


def complete_job(job_id: str, result: dict):
    """Marca um job como completo"""
    if job_id in jobs_db:
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["result"] = result
        jobs_db[job_id]["progress"] = {"status": "completed", "percentage": 100}


def fail_job(job_id: str, error: str):
    """Marca um job como erro"""
    if job_id in jobs_db:
        jobs_db[job_id]["status"] = "error"
        jobs_db[job_id]["error"] = error


async def run_download_job(job_id: str, url: str, request: DownloadRequest):
    """Executa o download em background"""
    try:
        # Criar settings a partir do request
        settings = Settings(
            out_dir=request.out_dir,
            archive_file=request.archive_file,
            fmt=request.fmt,
            max_res=request.max_res,
            subs=request.subs,
            auto_subs=request.auto_subs,
            sub_langs=request.sub_langs,
            thumbnails=request.thumbnails,
            audio_only=request.audio_only,
            workers=1,  # API sempre usa 1 worker
            limit=request.limit,
            dry_run=False,
            drive_upload=False,  # Desabilitado por padrão na API
            drive_root="YouTubeArchive",
            drive_credentials="./credentials.json",
            drive_token="./token.json",
            uploaded_log="./uploaded.jsonl",
            cookies_file=request.cookies_file,
            referer=request.referer,
            origin=request.origin,
            user_agent=request.user_agent,
            concurrent_fragments=request.concurrent_fragments,
            custom_path=request.path,
            file_name=request.file_name,
            archive_id=request.archive_id,
            delay_between_downloads=request.delay_between_downloads,
            batch_size=request.batch_size,
            batch_delay=request.batch_delay,
            randomize_delay=request.randomize_delay,
        )

        # Criar diretório de saída
        target_dir = os.path.join(request.out_dir, request.path) if request.path else request.out_dir
        os.makedirs(target_dir, exist_ok=True)

        # Executar download com callback de progresso
        def progress_callback(progress: dict):
            update_job_progress(job_id, progress)

        # Executar em thread separada para não bloquear
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            download_video,
            url,
            settings,
            progress_callback,
        )

        if result["status"] == "error":
            fail_job(job_id, result.get("error", "Unknown error"))
        else:
            complete_job(job_id, result)

    except Exception as e:
        fail_job(job_id, str(e))


# ========== Endpoints ==========

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "ok",
        "service": "YT-Archiver API",
        "version": "2.0.0",
    }


@app.post("/api/video-info")
async def video_info(request: VideoInfoRequest):
    """Obtém informações sobre um vídeo sem baixar"""
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, get_video_info, request.url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/download")
async def start_download(request: DownloadRequest):
    """Inicia um download em background"""
    try:
        # Criar job
        job_id = create_job(request.url, request)

        # Criar task assíncrona
        task = asyncio.create_task(run_download_job(job_id, request.url, request))
        active_tasks[job_id] = task

        return {
            "status": "success",
            "job_id": job_id,
            "message": "Download iniciado",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Obtém o status de um job"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    return jobs_db[job_id]


@app.get("/api/jobs")
async def list_jobs():
    """Lista todos os jobs"""
    return {
        "total": len(jobs_db),
        "jobs": list(jobs_db.values()),
    }


@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancela um job em execução"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    job = jobs_db[job_id]

    # Só pode cancelar jobs que estão rodando
    if job["status"] not in ["pending", "downloading"]:
        raise HTTPException(status_code=400, detail="Job não está em execução")

    # Cancelar a task se existir
    if job_id in active_tasks:
        task = active_tasks[job_id]
        task.cancel()
        del active_tasks[job_id]

    # Marcar como cancelado
    jobs_db[job_id]["status"] = "cancelled"
    jobs_db[job_id]["error"] = "Download cancelado pelo usuário"

    return {"status": "success", "message": "Download cancelado"}


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Remove um job do histórico"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    # Cancelar primeiro se estiver rodando
    if job_id in active_tasks:
        task = active_tasks[job_id]
        task.cancel()
        del active_tasks[job_id]

    del jobs_db[job_id]
    return {"status": "success", "message": "Job removido"}


@app.get("/api/jobs/{job_id}/stream")
async def stream_job_progress(job_id: str):
    """
    Stream de progresso em tempo real usando Server-Sent Events (SSE)
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job não encontrado")

    async def event_generator():
        last_progress = None
        while True:
            job = jobs_db.get(job_id)
            if not job:
                break

            current_progress = job.get("progress", {})

            # Enviar update se houver mudança
            if current_progress != last_progress:
                import json
                yield f"data: {json.dumps(job)}\n\n"
                last_progress = current_progress.copy()

            # Parar se job terminou
            if job["status"] in ["completed", "error"]:
                break

            await asyncio.sleep(0.5)  # Poll a cada 500ms

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ========== Video Library Endpoints ==========

def scan_videos_directory(base_dir: str = "./downloads") -> List[dict]:
    """
    Escaneia o diretório de downloads e retorna lista de vídeos com metadados.
    Estrutura esperada: downloads/[channel]/[subcategory]/video.mp4
    """
    videos = []
    base_path = Path(base_dir)

    if not base_path.exists():
        return videos

    # Extensões de vídeo suportadas
    video_extensions = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.flv', '.wmv'}

    # Escanear recursivamente
    for video_file in base_path.rglob('*'):
        if video_file.suffix.lower() in video_extensions:
            # Calcular o caminho relativo
            rel_path = video_file.relative_to(base_path)
            parts = rel_path.parts

            # Extrair "canal" (primeira pasta na hierarquia)
            channel = parts[0] if len(parts) > 1 else "Sem categoria"

            # Nome do vídeo (sem extensão)
            title = video_file.stem

            # Procurar thumbnail
            thumbnail = None
            for thumb_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                thumb_path = video_file.with_suffix(thumb_ext)
                if thumb_path.exists():
                    thumbnail = str(thumb_path.relative_to(base_path))
                    break

            # Informações do arquivo
            stat = video_file.stat()

            videos.append({
                "id": str(rel_path),  # Usar caminho relativo como ID
                "title": title,
                "channel": channel,
                "path": str(rel_path),
                "thumbnail": thumbnail,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

    # Ordenar por data de modificação (mais recentes primeiro)
    videos.sort(key=lambda x: x["modified_at"], reverse=True)

    return videos


@app.get("/api/videos")
async def list_videos(base_dir: str = "./downloads"):
    """Lista todos os vídeos disponíveis na biblioteca"""
    try:
        videos = scan_videos_directory(base_dir)
        return {
            "total": len(videos),
            "videos": videos,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/videos/stream/{video_path:path}")
async def stream_video(video_path: str, base_dir: str = "./downloads"):
    """
    Serve o arquivo de vídeo para streaming.
    Suporta range requests para seek/skip.
    """
    try:
        # Decodificar e sanitizar o path
        video_path = unquote(video_path)
        full_path = Path(base_dir) / video_path

        # Validar que o arquivo existe e está dentro do base_dir (segurança)
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="Vídeo não encontrado")

        if not str(full_path.resolve()).startswith(str(Path(base_dir).resolve())):
            raise HTTPException(status_code=403, detail="Acesso negado")

        return FileResponse(
            full_path,
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Disposition": f'inline; filename="{full_path.name}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/videos/thumbnail/{thumbnail_path:path}")
async def get_thumbnail(thumbnail_path: str, base_dir: str = "./downloads"):
    """Serve a thumbnail do vídeo"""
    try:
        # Decodificar e sanitizar o path
        thumbnail_path = unquote(thumbnail_path)
        full_path = Path(base_dir) / thumbnail_path

        # Validar que o arquivo existe e está dentro do base_dir (segurança)
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="Thumbnail não encontrada")

        if not str(full_path.resolve()).startswith(str(Path(base_dir).resolve())):
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Detectar tipo MIME baseado na extensão
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
        }
        media_type = mime_types.get(full_path.suffix.lower(), 'image/jpeg')

        return FileResponse(full_path, media_type=media_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/videos/{video_path:path}")
async def delete_video(video_path: str, base_dir: str = "./downloads"):
    """
    Exclui um vídeo e seus arquivos associados (thumbnail, legendas, etc).
    """
    try:
        # Decodificar e sanitizar o path
        video_path = unquote(video_path)
        full_path = Path(base_dir) / video_path

        # Validar que o arquivo existe e está dentro do base_dir (segurança)
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Vídeo não encontrado")

        if not str(full_path.resolve()).startswith(str(Path(base_dir).resolve())):
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Listar arquivos relacionados (mesmo nome, extensões diferentes)
        related_files = []
        base_name = full_path.stem
        parent_dir = full_path.parent

        # Procurar por thumbnails, legendas, info.json, etc
        # Usar iterdir() em vez de glob() porque glob falha com caracteres especiais como [] no nome
        for file in parent_dir.iterdir():
            if file.is_file():
                # Checar se o nome do arquivo começa com o base_name
                # Isso captura extensões simples (.mp4, .webp) e compostas (.info.json, .pt-BR.vtt)
                if file.name.startswith(base_name + "."):
                    related_files.append(file)

        # Extrair ID do vídeo do nome do arquivo para remover do archive
        # O ID geralmente está entre colchetes no final do nome, ex: [FGM3U3buQj0]
        import re
        video_id = None
        match = re.search(r'\[([^\]]+)\]', base_name)
        if match:
            video_id = match.group(1)

        # Excluir todos os arquivos relacionados
        deleted_files = []
        for file in related_files:
            try:
                file.unlink()
                deleted_files.append(str(file.relative_to(base_dir)))
            except Exception as e:
                print(f"Erro ao excluir {file}: {e}")

        # Remover do arquivo de controle (archive.txt) se encontrou o ID
        archive_file = Path("./archive.txt")
        if video_id and archive_file.exists():
            try:
                # Ler todas as linhas
                with open(archive_file, "r") as f:
                    lines = f.readlines()

                # Filtrar linhas que não contêm o video_id
                filtered_lines = [line for line in lines if video_id not in line]

                # Reescrever o arquivo sem o vídeo excluído
                with open(archive_file, "w") as f:
                    f.writelines(filtered_lines)

                print(f"Removido '{video_id}' do arquivo de controle")
            except Exception as e:
                print(f"Erro ao remover do arquivo de controle: {e}")

        # Tentar remover diretórios vazios (cleanup)
        try:
            if parent_dir != Path(base_dir) and not any(parent_dir.iterdir()):
                parent_dir.rmdir()
                # Tentar remover o pai também se estiver vazio
                grandparent = parent_dir.parent
                if grandparent != Path(base_dir) and not any(grandparent.iterdir()):
                    grandparent.rmdir()
        except:
            pass

        return {
            "status": "success",
            "message": "Vídeo excluído com sucesso",
            "deleted_files": deleted_files,
            "removed_from_archive": video_id is not None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

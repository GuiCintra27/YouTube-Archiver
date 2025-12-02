"""
Drive service - business logic for Google Drive integration
"""
import re
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Generator
import requests

from google.oauth2.credentials import Credentials

from .manager import drive_manager, SCOPES
from app.core.security import validate_path_within_base, validate_file_exists, sanitize_path
# Import store directly to avoid circular imports via app.jobs package
from app.jobs.store import JobType
import app.jobs.store as store

# Semaphore para limitar uploads concorrentes (3 simultâneos)
UPLOAD_SEMAPHORE: Optional[asyncio.Semaphore] = None


def _update_job_progress(job_id: str, progress: Dict) -> None:
    """Update the progress of a drive upload job."""
    job = store.get_job(job_id)
    if job:
        job["progress"] = progress
        if progress.get("status") == "uploading":
            job["status"] = "uploading"


def _complete_job(job_id: str, result: Dict) -> None:
    """Mark a drive upload job as completed."""
    job = store.get_job(job_id)
    if job:
        job["status"] = "completed"
        job["result"] = result
        job["progress"]["status"] = "completed"
        job["progress"]["percent"] = 100
        job["completed_at"] = datetime.now().isoformat()


def _fail_job(job_id: str, error: str) -> None:
    """Mark a drive upload job as failed."""
    job = store.get_job(job_id)
    if job:
        job["status"] = "error"
        job["error"] = error
        job["completed_at"] = datetime.now().isoformat()


def _get_upload_semaphore() -> asyncio.Semaphore:
    """Get or create the upload semaphore (must be created in event loop context)."""
    global UPLOAD_SEMAPHORE
    if UPLOAD_SEMAPHORE is None:
        UPLOAD_SEMAPHORE = asyncio.Semaphore(3)
    return UPLOAD_SEMAPHORE


def get_auth_status() -> Dict:
    """Get authentication status"""
    return {
        "authenticated": drive_manager.is_authenticated(),
        "credentials_exists": drive_manager.credentials_exist(),
    }


def get_auth_url() -> str:
    """Get OAuth authorization URL"""
    return drive_manager.get_auth_url()


def exchange_auth_code(code: str) -> Dict:
    """Exchange authorization code for tokens"""
    result = drive_manager.exchange_code(code)
    return {
        "status": "success",
        "message": "Autenticação concluída com sucesso!",
        **result
    }


def list_videos_paginated(page: int = 1, limit: int = 24) -> Dict:
    """List Drive videos with pagination"""
    videos = drive_manager.list_videos()
    total = len(videos)

    start = (page - 1) * limit
    end = start + limit
    page_videos = videos[start:end]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "videos": page_videos
    }


def upload_video(video_path: str, base_dir: str = "./downloads") -> Dict:
    """Upload a local video to Drive (síncrono)"""
    video_path = sanitize_path(video_path)
    full_path = Path(base_dir) / video_path
    base_path = Path(base_dir)

    validate_file_exists(full_path)
    validate_path_within_base(full_path, base_path)

    return drive_manager.upload_video(
        local_path=str(full_path),
        relative_path=video_path
    )


async def upload_single_video(video_path: str, base_dir: str = "./downloads") -> str:
    """
    Upload assíncrono de um único vídeo.

    Retorna job_id imediatamente. O upload acontece em background.

    Args:
        video_path: Caminho relativo do vídeo
        base_dir: Diretório base dos vídeos locais

    Returns:
        job_id: ID único do job para acompanhamento via polling
    """
    video_path = sanitize_path(video_path)
    full_path = Path(base_dir) / video_path
    base_path = Path(base_dir)

    validate_file_exists(full_path)
    validate_path_within_base(full_path, base_path)

    job_id = str(uuid.uuid4())

    # Criar job no store
    job_data = {
        "job_id": job_id,
        "type": JobType.DRIVE_UPLOAD.value,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "progress": {
            "status": "initializing",
            "total": 1,
            "uploaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": video_path
        },
        "result": None,
        "error": None
    }
    store.set_job(job_id, job_data)

    # Iniciar task em background
    task = asyncio.create_task(_run_single_upload_job(job_id, str(full_path), video_path))
    store.set_task(job_id, task)

    return job_id


async def _run_single_upload_job(job_id: str, full_path: str, video_path: str) -> None:
    """Executa upload de um único arquivo em background."""
    try:
        # Atualizar progresso
        _update_job_progress(job_id, {
            "status": "uploading",
            "total": 1,
            "uploaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": video_path
        })

        # Upload usando thread para não bloquear event loop
        result = await asyncio.to_thread(
            drive_manager.upload_video,
            full_path,
            video_path
        )

        if result.get("status") != "error":
            _complete_job(job_id, {
                "status": "success",
                "uploaded": 1,
                "total": 1,
                "failed": []
            })
        else:
            _fail_job(job_id, result.get("message", "Upload failed"))

    except Exception as e:
        _fail_job(job_id, str(e))


def get_sync_status(base_dir: str = "./downloads") -> Dict:
    """Get sync status between local and Drive"""
    return drive_manager.get_sync_state(base_dir)


async def sync_all_videos(base_dir: str = "./downloads") -> str:
    """
    Inicia sincronização assíncrona de vídeos locais para o Drive.

    Retorna job_id imediatamente. O upload acontece em background
    com até 3 uploads simultâneos controlados por semaphore.

    Args:
        base_dir: Diretório base dos vídeos locais

    Returns:
        job_id: ID único do job para acompanhamento via polling
    """
    job_id = str(uuid.uuid4())

    # Criar job no store
    job_data = {
        "job_id": job_id,
        "type": JobType.DRIVE_SYNC.value,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "progress": {
            "status": "initializing",
            "total": 0,
            "uploaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": None,
            "files_in_progress": []
        },
        "result": None,
        "error": None
    }
    store.set_job(job_id, job_data)

    # Iniciar task em background
    task = asyncio.create_task(_run_batch_upload_job(job_id, base_dir))
    store.set_task(job_id, task)

    return job_id


async def _run_batch_upload_job(job_id: str, base_dir: str) -> None:
    """
    Executa uploads em paralelo com limite de 3 simultâneos.

    Esta função roda em background e atualiza o progresso do job
    conforme os uploads são processados.
    """
    try:
        # Obter lista de arquivos para upload
        sync_state = drive_manager.get_sync_state(base_dir)
        local_only = sync_state["local_only"]
        total = len(local_only)

        if total == 0:
            _complete_job(job_id, {
                "status": "success",
                "uploaded": 0,
                "total": 0,
                "failed": []
            })
            return

        # Atualizar progresso inicial
        _update_job_progress(job_id, {
            "status": "uploading",
            "total": total,
            "uploaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": None,
            "files_in_progress": []
        })

        # Contadores thread-safe
        results = {"uploaded": 0, "failed": []}
        results_lock = asyncio.Lock()
        files_in_progress: List[str] = []
        progress_lock = asyncio.Lock()

        semaphore = _get_upload_semaphore()

        async def upload_with_semaphore(video_path: str) -> None:
            """Upload um arquivo com controle de concorrência."""
            async with semaphore:
                # Verificar se job foi cancelado
                job = store.get_job(job_id)
                if job and job.get("status") == "cancelled":
                    return

                # Marcar arquivo como em progresso
                async with progress_lock:
                    files_in_progress.append(video_path)
                    current_job = store.get_job(job_id)
                    if current_job:
                        current_job["progress"]["current_file"] = video_path
                        current_job["progress"]["files_in_progress"] = files_in_progress.copy()

                try:
                    # Upload usando thread para não bloquear event loop
                    full_path = str(Path(base_dir) / video_path)
                    result = await asyncio.to_thread(
                        drive_manager.upload_video,
                        full_path,
                        video_path
                    )

                    async with results_lock:
                        if result.get("status") != "error":
                            results["uploaded"] += 1
                        else:
                            results["failed"].append({
                                "file": video_path,
                                "error": result.get("message", "Unknown error")
                            })

                        # Atualizar progresso geral
                        done = results["uploaded"] + len(results["failed"])
                        _update_job_progress(job_id, {
                            "status": "uploading",
                            "total": total,
                            "uploaded": results["uploaded"],
                            "failed": len(results["failed"]),
                            "percent": (done / total) * 100,
                            "current_file": None,
                            "files_in_progress": []
                        })

                except Exception as e:
                    async with results_lock:
                        results["failed"].append({
                            "file": video_path,
                            "error": str(e)
                        })
                finally:
                    # Remover arquivo da lista de em progresso
                    async with progress_lock:
                        if video_path in files_in_progress:
                            files_in_progress.remove(video_path)

        # Criar todas as tasks (semaphore controla concorrência)
        tasks = [
            upload_with_semaphore(video_path)
            for video_path in local_only
        ]

        # Aguardar todas completarem
        await asyncio.gather(*tasks, return_exceptions=True)

        # Completar job
        _complete_job(job_id, {
            "status": "success",
            "uploaded": results["uploaded"],
            "total": total,
            "failed": results["failed"]
        })

    except Exception as e:
        _fail_job(job_id, str(e))


def delete_video(file_id: str) -> Dict:
    """Delete a video from Drive"""
    success = drive_manager.delete_video(file_id)

    if not success:
        raise Exception("Failed to delete video")

    return {
        "status": "success",
        "message": "Video deleted from Drive"
    }


def delete_videos_batch(file_ids: List[str]) -> Dict:
    """
    Delete multiple videos from Drive.

    Args:
        file_ids: List of file IDs to delete

    Returns:
        Dict with deletion results
    """
    if not file_ids:
        return {
            "status": "success",
            "message": "No files to delete",
            "total_deleted": 0,
            "total_failed": 0,
        }

    result = drive_manager.delete_videos_batch(file_ids)

    status = "success" if result["total_failed"] == 0 else "partial"
    message = f"{result['total_deleted']} vídeo(s) excluído(s)"
    if result["total_failed"] > 0:
        message += f", {result['total_failed']} falha(s)"

    return {
        "status": status,
        "message": message,
        **result,
    }


def stream_video(
    file_id: str,
    range_header: Optional[str] = None
) -> tuple[Generator, Dict, int]:
    """
    Stream video from Drive with range request support.

    Returns:
        Tuple of (generator, headers dict, status code)
    """
    file_metadata = drive_manager.get_file_metadata(file_id)
    file_size = int(file_metadata.get('size', 0))
    mime_type = file_metadata.get('mimeType', 'video/mp4')

    # Get credentials for direct request
    creds = Credentials.from_authorized_user_file(
        drive_manager.token_path,
        SCOPES
    )

    download_url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'
    auth_headers = {'Authorization': f'Bearer {creds.token}'}

    if range_header:
        # Add Range header to request
        auth_headers['Range'] = range_header

        # Parse Range header for Content-Range
        range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1

            # Validate range
            if start >= file_size or end >= file_size or start > end:
                return None, {"Content-Range": f"bytes */{file_size}"}, 416

            # Make request with Range to Drive
            response = requests.get(download_url, headers=auth_headers, stream=True)

            def iterfile():
                for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                    if chunk:
                        yield chunk

            content_length = end - start + 1
            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": mime_type,
                "Cache-Control": "public, max-age=3600",
            }

            return iterfile(), headers, 206

    # No Range header - full streaming
    response = requests.get(download_url, headers=auth_headers, stream=True)

    def iterfile():
        for chunk in response.iter_content(chunk_size=2*1024*1024):  # 2MB chunks
            if chunk:
                yield chunk

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": mime_type,
        "Cache-Control": "public, max-age=3600",
    }

    return iterfile(), headers, 200


def get_thumbnail(file_id: str) -> Optional[bytes]:
    """Get thumbnail bytes for a video"""
    return drive_manager.get_thumbnail(file_id)


def get_custom_thumbnail(file_id: str) -> Optional[tuple[bytes, str]]:
    """
    Get custom thumbnail file (image) directly from Drive.
    Returns tuple of (bytes, mime_type) or None if not available.
    """
    return drive_manager.get_image_file(file_id)


async def upload_external_files(
    folder_name: str,
    temp_files: List[str],
) -> str:
    """
    Upload de arquivos externos para uma pasta específica no Drive.

    Args:
        folder_name: Nome da pasta de destino no Drive
        temp_files: Lista de caminhos dos arquivos temporários

    Returns:
        job_id: ID único do job para acompanhamento via polling
    """
    job_id = str(uuid.uuid4())

    # Criar job no store
    job_data = {
        "job_id": job_id,
        "type": JobType.DRIVE_UPLOAD.value,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "progress": {
            "status": "initializing",
            "total": len(temp_files),
            "uploaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": None,
            "folder_name": folder_name
        },
        "result": None,
        "error": None
    }
    store.set_job(job_id, job_data)

    # Iniciar task em background
    task = asyncio.create_task(_run_external_upload_job(job_id, folder_name, temp_files))
    store.set_task(job_id, task)

    return job_id


async def _run_external_upload_job(
    job_id: str,
    folder_name: str,
    temp_files: List[str]
) -> None:
    """
    Executa upload de arquivos externos em background.

    Após o upload, limpa os arquivos temporários.
    """
    try:
        total = len(temp_files)

        # Atualizar progresso
        _update_job_progress(job_id, {
            "status": "uploading",
            "total": total,
            "uploaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": None,
            "folder_name": folder_name
        })

        def progress_callback(progress: Dict) -> None:
            """Callback para atualizar progresso durante upload."""
            _update_job_progress(job_id, {
                "status": "uploading",
                "total": total,
                "uploaded": progress.get("files_uploaded", 0),
                "failed": 0,
                "percent": progress.get("overall_progress", 0),
                "current_file": progress.get("current_file"),
                "folder_name": folder_name
            })

        # Upload usando thread para não bloquear event loop
        result = await asyncio.to_thread(
            drive_manager.upload_to_folder,
            folder_name,
            temp_files,
            progress_callback
        )

        # Get generated thumbnails for cleanup
        generated_thumbnails = result.get("generated_thumbnails", [])

        # Completar job
        _complete_job(job_id, {
            "status": result.get("status", "success"),
            "folder_name": folder_name,
            "folder_id": result.get("folder_id"),
            "uploaded": result.get("total_uploaded", 0),
            "skipped": result.get("total_skipped", 0),
            "total": total,
            "failed": result.get("failed", []),
            "files": result.get("uploaded", []),
            "thumbnails_generated": len(generated_thumbnails),
        })

    except Exception as e:
        _fail_job(job_id, str(e))
        generated_thumbnails = []

    finally:
        # Limpar arquivos temporários
        for temp_file in temp_files:
            try:
                temp_path = Path(temp_file)
                if temp_path.exists():
                    temp_path.unlink()
            except Exception:
                pass

        # Limpar thumbnails geradas automaticamente
        for thumb_file in generated_thumbnails:
            try:
                thumb_path = Path(thumb_file)
                if thumb_path.exists():
                    thumb_path.unlink()
            except Exception:
                pass

        # Limpar diretório temporário se estiver vazio
        try:
            temp_dir = Path("/tmp/yt-archiver-upload")
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()
        except Exception:
            pass


# ==================== Download Functions ====================

# Semaphore para limitar downloads concorrentes (3 simultâneos)
DOWNLOAD_SEMAPHORE: Optional[asyncio.Semaphore] = None


def _get_download_semaphore() -> asyncio.Semaphore:
    """Get or create the download semaphore (must be created in event loop context)."""
    global DOWNLOAD_SEMAPHORE
    if DOWNLOAD_SEMAPHORE is None:
        DOWNLOAD_SEMAPHORE = asyncio.Semaphore(3)
    return DOWNLOAD_SEMAPHORE


async def download_single_from_drive(
    file_id: str,
    relative_path: str,
    base_dir: str = "./downloads"
) -> str:
    """
    Download assíncrono de um único vídeo do Drive para o local.

    Args:
        file_id: ID do arquivo no Drive
        relative_path: Caminho relativo do arquivo no Drive
        base_dir: Diretório base local

    Returns:
        job_id: ID único do job para acompanhamento via polling
    """
    job_id = str(uuid.uuid4())

    # Criar job no store
    job_data = {
        "job_id": job_id,
        "type": JobType.DRIVE_DOWNLOAD.value,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "progress": {
            "status": "initializing",
            "total": 1,
            "downloaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": relative_path
        },
        "result": None,
        "error": None
    }
    store.set_job(job_id, job_data)

    # Iniciar task em background
    task = asyncio.create_task(
        _run_single_download_job(job_id, file_id, relative_path, base_dir)
    )
    store.set_task(job_id, task)

    return job_id


async def _run_single_download_job(
    job_id: str,
    file_id: str,
    relative_path: str,
    base_dir: str
) -> None:
    """Executa download de um único arquivo em background."""
    try:
        # Atualizar progresso
        _update_download_progress(job_id, {
            "status": "downloading",
            "total": 1,
            "downloaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": relative_path
        })

        def progress_callback(progress: Dict) -> None:
            _update_download_progress(job_id, {
                "status": "downloading",
                "total": 1,
                "downloaded": 0,
                "failed": 0,
                "percent": progress.get("progress", 0),
                "current_file": progress.get("file_name", relative_path)
            })

        # Download usando thread para não bloquear event loop
        result = await asyncio.to_thread(
            drive_manager.download_file,
            file_id,
            relative_path,
            base_dir,
            progress_callback
        )

        if result.get("status") != "error":
            _complete_download_job(job_id, {
                "status": "success",
                "downloaded": 1,
                "total": 1,
                "failed": [],
                "files": [result]
            })
        else:
            _fail_job(job_id, result.get("message", "Download failed"))

    except Exception as e:
        _fail_job(job_id, str(e))


async def download_all_from_drive(base_dir: str = "./downloads") -> str:
    """
    Download assíncrono de todos os vídeos que estão apenas no Drive.

    Retorna job_id imediatamente. O download acontece em background
    com até 3 downloads simultâneos controlados por semaphore.

    Args:
        base_dir: Diretório base local para downloads

    Returns:
        job_id: ID único do job para acompanhamento via polling
    """
    job_id = str(uuid.uuid4())

    # Criar job no store
    job_data = {
        "job_id": job_id,
        "type": JobType.DRIVE_DOWNLOAD.value,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "progress": {
            "status": "initializing",
            "total": 0,
            "downloaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": None,
            "files_in_progress": []
        },
        "result": None,
        "error": None
    }
    store.set_job(job_id, job_data)

    # Iniciar task em background
    task = asyncio.create_task(_run_batch_download_job(job_id, base_dir))
    store.set_task(job_id, task)

    return job_id


async def _run_batch_download_job(job_id: str, base_dir: str) -> None:
    """
    Executa downloads em paralelo com limite de 3 simultâneos.
    """
    try:
        # Obter lista de arquivos para download (apenas no Drive)
        sync_state = drive_manager.get_sync_state(base_dir)
        drive_only = sync_state["drive_only"]
        total = len(drive_only)

        if total == 0:
            _complete_download_job(job_id, {
                "status": "success",
                "downloaded": 0,
                "total": 0,
                "failed": []
            })
            return

        # Atualizar progresso inicial
        _update_download_progress(job_id, {
            "status": "downloading",
            "total": total,
            "downloaded": 0,
            "failed": 0,
            "percent": 0,
            "current_file": None,
            "files_in_progress": []
        })

        # Obter lista de vídeos do Drive com IDs
        drive_videos = drive_manager.list_videos()
        path_to_video = {v['path']: v for v in drive_videos}

        # Contadores thread-safe
        results = {"downloaded": 0, "failed": [], "files": []}
        results_lock = asyncio.Lock()
        files_in_progress: List[str] = []
        progress_lock = asyncio.Lock()

        semaphore = _get_download_semaphore()

        async def download_with_semaphore(video_path: str) -> None:
            """Download um arquivo com controle de concorrência."""
            async with semaphore:
                # Verificar se job foi cancelado
                job = store.get_job(job_id)
                if job and job.get("status") == "cancelled":
                    return

                # Obter ID do arquivo
                video_info = path_to_video.get(video_path)
                if not video_info:
                    async with results_lock:
                        results["failed"].append({
                            "file": video_path,
                            "error": "Video not found in Drive"
                        })
                    return

                file_id = video_info['id']

                # Marcar arquivo como em progresso
                async with progress_lock:
                    files_in_progress.append(video_path)
                    current_job = store.get_job(job_id)
                    if current_job:
                        current_job["progress"]["current_file"] = video_path
                        current_job["progress"]["files_in_progress"] = files_in_progress.copy()

                try:
                    # Download usando thread para não bloquear event loop
                    result = await asyncio.to_thread(
                        drive_manager.download_file,
                        file_id,
                        video_path,
                        base_dir,
                        None  # No progress callback for batch
                    )

                    async with results_lock:
                        if result.get("status") != "error":
                            results["downloaded"] += 1
                            results["files"].append(result)
                        else:
                            results["failed"].append({
                                "file": video_path,
                                "error": result.get("message", "Unknown error")
                            })

                        # Atualizar progresso geral
                        done = results["downloaded"] + len(results["failed"])
                        _update_download_progress(job_id, {
                            "status": "downloading",
                            "total": total,
                            "downloaded": results["downloaded"],
                            "failed": len(results["failed"]),
                            "percent": (done / total) * 100,
                            "current_file": None,
                            "files_in_progress": []
                        })

                except Exception as e:
                    async with results_lock:
                        results["failed"].append({
                            "file": video_path,
                            "error": str(e)
                        })
                finally:
                    # Remover arquivo da lista de em progresso
                    async with progress_lock:
                        if video_path in files_in_progress:
                            files_in_progress.remove(video_path)

        # Criar todas as tasks (semaphore controla concorrência)
        tasks = [
            download_with_semaphore(video_path)
            for video_path in drive_only
        ]

        # Aguardar todas completarem
        await asyncio.gather(*tasks, return_exceptions=True)

        # Completar job
        _complete_download_job(job_id, {
            "status": "success",
            "downloaded": results["downloaded"],
            "total": total,
            "failed": results["failed"],
            "files": results["files"]
        })

    except Exception as e:
        _fail_job(job_id, str(e))


def _update_download_progress(job_id: str, progress: Dict) -> None:
    """Update the progress of a drive download job."""
    job = store.get_job(job_id)
    if job:
        job["progress"] = progress
        if progress.get("status") == "downloading":
            job["status"] = "downloading"


def _complete_download_job(job_id: str, result: Dict) -> None:
    """Mark a drive download job as completed."""
    job = store.get_job(job_id)
    if job:
        job["status"] = "completed"
        job["result"] = result
        job["progress"]["status"] = "completed"
        job["progress"]["percent"] = 100
        job["completed_at"] = datetime.now().isoformat()

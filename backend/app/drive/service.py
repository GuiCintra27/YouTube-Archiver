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
from app.config import settings
from app.core.blocking import run_blocking, get_drive_semaphore, get_catalog_semaphore
from app.core.security import validate_path_within_base, validate_file_exists, sanitize_path
from app.core.logging import get_module_logger
from app.core.http import request_with_retry
from app.catalog.repository import CatalogRepository
from app.catalog.service import (
    list_drive_videos_paginated,
    delete_drive_video_from_catalog,
    maybe_publish_drive_snapshot,
    rename_drive_video_in_catalog,
    set_drive_thumbnail_in_catalog,
    set_drive_share_metadata_in_catalog,
    clear_drive_share_metadata_in_catalog,
    upsert_drive_video_from_upload,
)
from app.catalog.service import upsert_local_video_from_fs
# Import store directly to avoid circular imports via app.jobs package
from app.jobs.store import JobType
import app.jobs.store as store

logger = get_module_logger("drive.service")

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


async def _run_drive_cleanup_job(job_id: str, folder_ids: List[str]) -> None:
    try:
        job = store.get_job(job_id)
        if job:
            job["status"] = "running"
            job["progress"]["status"] = "running"

        result = await run_blocking(
            drive_manager.cleanup_empty_folders,
            folder_ids,
            semaphore=get_drive_semaphore(),
            label="drive.cleanup_folders",
        )

        job = store.get_job(job_id)
        if job:
            job["status"] = "completed"
            job["result"] = result
            job["progress"]["status"] = "completed"
            job["progress"]["folders_deleted"] = len(result.get("deleted", []))
            job["completed_at"] = datetime.now().isoformat()
    except Exception as e:
        job = store.get_job(job_id)
        if job:
            job["status"] = "error"
            job["error"] = str(e)
            job["completed_at"] = datetime.now().isoformat()


def _enqueue_drive_cleanup(folder_ids: List[str]) -> Optional[str]:
    if not folder_ids:
        return None

    job_id = str(uuid.uuid4())
    job_data = {
        "job_id": job_id,
        "type": JobType.DRIVE_CLEANUP.value,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "progress": {
            "status": "queued",
            "folders_total": len(folder_ids),
            "folders_deleted": 0,
        },
        "result": None,
        "error": None,
    }
    store.set_job(job_id, job_data)

    task = asyncio.create_task(_run_drive_cleanup_job(job_id, folder_ids))
    store.set_task(job_id, task)
    return job_id


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


async def list_videos_paginated(page: int = 1, limit: int = 24) -> Dict:
    """
    List Drive videos with pagination.

    Uses SQLite cache if enabled for faster response.
    Falls back to direct API if cache is unavailable.
    """
    if settings.CATALOG_ENABLED:
        result = await list_drive_videos_paginated(page=page, limit=limit)
        if result.get("total", 0) > 0:
            return result
        # Drive catalog is empty: avoid slow legacy listing unless explicitly allowed.
        if not settings.CATALOG_DRIVE_ALLOW_LEGACY_LISTING_FALLBACK:
            return {
                "total": 0,
                "page": page,
                "limit": limit,
                "videos": [],
                "warning": "Drive catalog vazio. Rode /api/catalog/drive/rebuild (primeira vez) ou /api/catalog/drive/import (em uma máquina nova).",
            }

    # Check if cache is enabled
    if settings.DRIVE_CACHE_ENABLED:
        try:
            from .cache import get_repository, ensure_cache_initialized

            # Ensure cache has data (triggers initial sync if empty)
            await ensure_cache_initialized()

            repo = get_repository()
            result = await repo.get_videos_paginated(page, limit)

            if result and result.get("videos") is not None:
                logger.debug(f"Serving {len(result['videos'])} videos from cache")
                return result

        except Exception as e:
            logger.warning(f"Cache error, falling back to API: {e}")

            if not settings.DRIVE_CACHE_FALLBACK_TO_API:
                raise

    # Fallback to direct Drive API
    logger.debug("Fetching videos from Drive API")
    videos = await run_blocking(
        drive_manager.list_videos,
        semaphore=get_drive_semaphore(),
        label="drive.list_videos",
    )
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
            if settings.CATALOG_ENABLED:
                try:
                    video_file_id = result.get("file_id")
                    if video_file_id:
                        await upsert_drive_video_from_upload(
                            video_file_id=str(video_file_id),
                            drive_path=video_path,
                            size_bytes=int(result.get("size") or 0),
                            related_files=result.get("related_files_detailed") or [],
                        )
                        await maybe_publish_drive_snapshot(reason="drive_upload_single")
                except Exception as e:
                    logger.warning(f"Catalog write-through failed (drive_upload_single): {e}")

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


async def get_sync_status(base_dir: str = "./downloads") -> Dict:
    """Get sync status between local and Drive (catalog-first)."""
    if settings.CATALOG_ENABLED:
        return await run_blocking(
            get_sync_status_from_catalog,
            semaphore=get_catalog_semaphore(),
            label="drive.sync_status.catalog",
        )
    result = await run_blocking(
        drive_manager.get_sync_state,
        base_dir,
        semaphore=get_drive_semaphore(),
        label="drive.sync_status",
    )
    local_only = result.get("local_only") or []
    drive_only = result.get("drive_only") or []
    synced = result.get("synced") or []
    result.setdefault("local_only_count", len(local_only))
    result.setdefault("drive_only_count", len(drive_only))
    result.setdefault("synced_count", len(synced))
    result.setdefault("warnings", [])
    return result


def _get_catalog_sets(repo: CatalogRepository) -> tuple[set[str], dict[str, str]]:
    """
    Returns:
        local_paths_set: set[str]
        drive_path_to_file_id: dict[path -> file_id]
    """
    local_paths = repo.list_video_asset_paths(location="local")
    drive_assets = repo.list_drive_video_assets()

    local_set = set(local_paths)
    drive_map = {a["path"]: a["file_id"] for a in drive_assets if a.get("path") and a.get("file_id")}
    return local_set, drive_map


def get_sync_status_from_catalog() -> Dict:
    repo = CatalogRepository()
    counts = repo.get_counts()
    drive_state = repo.get_state("drive")
    drive_imported = bool(drive_state.get("last_imported_at"))
    local_set, drive_map = _get_catalog_sets(repo)
    drive_set = set(drive_map.keys())

    local_only_count = len(local_set - drive_set)
    drive_only_count = len(drive_set - local_set)
    synced_count = len(local_set & drive_set)

    warnings: list[str] = []
    if counts.get("drive", 0) == 0:
        if drive_imported:
            warnings.append("Catálogo do Drive vazio (importado). Você pode sincronizar para enviar seus vídeos.")
        else:
            warnings.append("Catálogo do Drive vazio: rode /api/catalog/drive/import (máquina nova) ou /api/catalog/drive/rebuild (primeira vez).")
    if counts.get("local", 0) == 0:
        warnings.append("Catálogo local vazio: rode /api/catalog/bootstrap-local para indexar seus vídeos locais.")

    return {
        "total_local": len(local_set),
        "total_drive": len(drive_set),
        "local_only_count": local_only_count,
        "drive_only_count": drive_only_count,
        "synced_count": synced_count,
        "warnings": warnings,
    }


async def get_sync_items_from_catalog(*, kind: str, page: int, limit: int) -> Dict:
    def _run() -> Dict:
        repo = CatalogRepository()
        local_set, drive_map = _get_catalog_sets(repo)
        drive_set = set(drive_map.keys())

        if kind == "local_only":
            all_items = sorted(local_set - drive_set)
            items = [{"path": p} for p in all_items]
        elif kind == "drive_only":
            all_paths = sorted(drive_set - local_set)
            items = [{"path": p, "file_id": drive_map.get(p)} for p in all_paths if drive_map.get(p)]
            all_items = items
        elif kind == "synced":
            all_items = sorted(local_set & drive_set)
            items = [{"path": p} for p in all_items]
        else:
            from app.core.exceptions import InvalidRequestException

            raise InvalidRequestException("kind inválido (use: local_only, drive_only, synced)")

        total = len(all_items)
        offset = (page - 1) * limit
        page_items = items[offset : offset + limit]

        return {"kind": kind, "total": total, "page": page, "limit": limit, "items": page_items}

    return await run_blocking(
        _run,
        semaphore=get_catalog_semaphore(),
        label="drive.sync_items",
    )


async def resolve_drive_file_id_by_path(*, drive_path: str) -> str:
    def _run() -> str:
        repo = CatalogRepository()
        file_id = repo.find_drive_file_id_by_path(drive_path)
        if not file_id:
            from app.core.exceptions import VideoNotFoundException

            raise VideoNotFoundException("Vídeo não encontrado no catálogo do Drive", path=drive_path)
        return file_id

    return await run_blocking(
        _run,
        semaphore=get_catalog_semaphore(),
        label="drive.resolve_path",
    )


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
        if settings.CATALOG_ENABLED:
            repo = CatalogRepository()
            counts = await run_blocking(
                repo.get_counts,
                semaphore=get_catalog_semaphore(),
                label="drive.sync.counts",
            )
            drive_state = await run_blocking(
                repo.get_state,
                "drive",
                semaphore=get_catalog_semaphore(),
                label="drive.sync.state",
            )
            drive_imported = bool(drive_state.get("last_imported_at"))
            if counts.get("local", 0) == 0:
                raise Exception("Catálogo local vazio: rode /api/catalog/bootstrap-local antes de sincronizar.")
            if counts.get("drive", 0) == 0 and not drive_imported:
                raise Exception("Catálogo do Drive vazio: rode /api/catalog/drive/import ou /api/catalog/drive/rebuild antes de sincronizar.")

            local_set, drive_map = await run_blocking(
                _get_catalog_sets,
                repo,
                semaphore=get_catalog_semaphore(),
                label="drive.sync.sets",
            )
            drive_set = set(drive_map.keys())
            local_only = sorted(local_set - drive_set)
        else:
            sync_state = await run_blocking(
                drive_manager.get_sync_state,
                base_dir,
                semaphore=get_drive_semaphore(),
                label="drive.sync_state",
            )
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
        catalog_state = {"changed": False}
        catalog_lock = asyncio.Lock()

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

                    if result.get("status") != "error" and settings.CATALOG_ENABLED:
                        async with catalog_lock:
                            try:
                                video_file_id = result.get("file_id")
                                if video_file_id:
                                    await upsert_drive_video_from_upload(
                                        video_file_id=str(video_file_id),
                                        drive_path=video_path,
                                        size_bytes=int(result.get("size") or 0),
                                        related_files=result.get("related_files_detailed") or [],
                                    )
                                    catalog_state["changed"] = True
                            except Exception as e:
                                logger.warning(f"Catalog write-through failed (drive_upload_batch): {e}")

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

        if settings.CATALOG_ENABLED and catalog_state["changed"]:
            await maybe_publish_drive_snapshot(reason="drive_upload_batch")

    except Exception as e:
        _fail_job(job_id, str(e))


async def delete_video(file_id: str) -> Dict:
    """Delete a video from Drive"""
    related_ids: List[str] = []
    if settings.CATALOG_ENABLED:
        def _get_related_ids() -> List[str]:
            repo = CatalogRepository()
            assets = repo.get_drive_assets_by_file_id(file_id)
            return [str(a["drive_file_id"]) for a in assets if a.get("drive_file_id")]

        related_ids = await run_blocking(
            _get_related_ids,
            semaphore=get_catalog_semaphore(),
            label="drive.delete.related_ids",
        )

    result = await run_blocking(
        drive_manager.delete_video_with_related,
        file_id,
        related_ids,
        semaphore=get_drive_semaphore(),
        label="drive.delete_video",
    )

    if not result.get("video_deleted"):
        raise Exception("Failed to delete video")

    if settings.CATALOG_ENABLED:
        try:
            await delete_drive_video_from_catalog(video_file_id=file_id)
            await maybe_publish_drive_snapshot(reason="drive_delete")
        except Exception as e:
            logger.warning(f"Catalog write-through failed (drive_delete): {e}")

    # Sync with cache
    if settings.DRIVE_CACHE_ENABLED:
        try:
            from .cache import sync_video_deleted
            await sync_video_deleted(file_id)
        except Exception as e:
            logger.warning(f"Failed to sync deletion to cache: {e}")

    cleanup_job_id = _enqueue_drive_cleanup(result.get("parent_ids") or [])

    return {
        "status": "success",
        "message": "Video deleted from Drive",
        "cleanup_job_id": cleanup_job_id,
        "deleted_related": max(0, result.get("total_deleted", 0) - 1),
    }


async def delete_videos_batch(file_ids: List[str]) -> Dict:
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

    related_map: Dict[str, List[str]] = {}
    if settings.CATALOG_ENABLED:
        def _get_related_map() -> Dict[str, List[str]]:
            repo = CatalogRepository()
            mapping: Dict[str, List[str]] = {}
            for vid in file_ids:
                assets = repo.get_drive_assets_by_file_id(vid)
                mapping[vid] = [str(a["drive_file_id"]) for a in assets if a.get("drive_file_id")]
            return mapping

        related_map = await run_blocking(
            _get_related_map,
            semaphore=get_catalog_semaphore(),
            label="drive.delete_batch.related_map",
        )

    result = await run_blocking(
        drive_manager.delete_videos_with_related,
        file_ids,
        related_map,
        semaphore=get_drive_semaphore(),
        label="drive.delete_batch",
    )

    deleted_video_ids = result.get("deleted_videos", [])

    if settings.CATALOG_ENABLED and deleted_video_ids:
        try:
            for deleted_id in deleted_video_ids:
                await delete_drive_video_from_catalog(video_file_id=deleted_id)
            await maybe_publish_drive_snapshot(reason="drive_delete_batch")
        except Exception as e:
            logger.warning(f"Catalog write-through failed (drive_delete_batch): {e}")

    # Sync with cache - mark deleted IDs
    if settings.DRIVE_CACHE_ENABLED and deleted_video_ids:
        try:
            from .cache import get_repository
            repo = get_repository()
            await repo.mark_videos_deleted_batch(deleted_video_ids)
        except Exception as e:
            logger.warning(f"Failed to sync batch deletion to cache: {e}")

    cleanup_job_id = _enqueue_drive_cleanup(result.get("parent_ids") or [])

    status = "success" if result["total_failed"] == 0 else "partial"
    message = f"{len(deleted_video_ids)} vídeo(s) excluído(s)"
    if result["total_failed"] > 0:
        message += f", {result['total_failed']} falha(s)"

    return {
        "status": status,
        "message": message,
        "cleanup_job_id": cleanup_job_id,
        **result,
    }


async def get_drive_share_status(file_id: str) -> Dict:
    """Get current public sharing status for a Drive file."""
    result = await run_blocking(
        drive_manager.get_share_status,
        file_id,
        semaphore=get_drive_semaphore(),
        label="drive.share.status",
    )

    return {
        "status": "success",
        "shared": bool(result.get("shared")),
        "link": result.get("link"),
    }


async def share_drive_video(file_id: str) -> Dict:
    """Enable public sharing for a Drive video."""
    result = await run_blocking(
        drive_manager.enable_share,
        file_id,
        semaphore=get_drive_semaphore(),
        label="drive.share.enable",
    )

    permission_id = result.get("permission_id")
    share_link = result.get("link")

    if settings.CATALOG_ENABLED and permission_id and share_link:
        try:
            await set_drive_share_metadata_in_catalog(
                video_file_id=file_id,
                share_link=str(share_link),
                permission_id=str(permission_id),
            )
        except Exception as e:
            logger.warning(f"Catalog write-through failed (drive_share_enable): {e}")

    return {
        "status": "success",
        "shared": True,
        "link": share_link,
    }


async def unshare_drive_video(file_id: str) -> Dict:
    """Disable public sharing for a Drive video."""
    await run_blocking(
        drive_manager.disable_share,
        file_id,
        semaphore=get_drive_semaphore(),
        label="drive.share.disable",
    )

    if settings.CATALOG_ENABLED:
        try:
            await clear_drive_share_metadata_in_catalog(video_file_id=file_id)
        except Exception as e:
            logger.warning(f"Catalog write-through failed (drive_share_disable): {e}")

    return {
        "status": "success",
        "shared": False,
        "link": None,
    }


def stream_video(
    file_id: str,
    range_header: Optional[str] = None,
    file_metadata: Optional[Dict] = None,
    access_token: Optional[str] = None,
) -> tuple[Generator, Dict, int]:
    """
    Stream video from Drive with range request support.

    Returns:
        Tuple of (generator, headers dict, status code)
    """
    file_metadata = file_metadata or drive_manager.get_file_metadata(file_id)
    file_size = int(file_metadata.get('size', 0))
    mime_type = file_metadata.get('mimeType', 'video/mp4')

    download_url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'
    if access_token:
        auth_headers = {'Authorization': f'Bearer {access_token}'}
    else:
        creds = Credentials.from_authorized_user_file(
            drive_manager.token_path,
            SCOPES
        )
        auth_headers = {'Authorization': f'Bearer {creds.token}'}

    if range_header:
        # Add Range header to request
        # Parse Range header for Content-Range
        range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1

            # Validate range
            if start >= file_size or end >= file_size or start > end:
                return None, {"Content-Range": f"bytes */{file_size}"}, 416

            def iterfile():
                request_headers = auth_headers.copy()
                request_headers['Range'] = range_header
                with request_with_retry(
                    "GET",
                    download_url,
                    headers=request_headers,
                    stream=True,
                    timeout=(settings.DRIVE_HTTP_TIMEOUT_CONNECT, settings.DRIVE_STREAM_TIMEOUT_READ),
                    retries=0,
                ) as response:
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
    def iterfile():
        with request_with_retry(
            "GET",
            download_url,
            headers=auth_headers,
            stream=True,
            timeout=(settings.DRIVE_HTTP_TIMEOUT_CONNECT, settings.DRIVE_STREAM_TIMEOUT_READ),
            retries=0,
        ) as response:
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


async def rename_drive_video(file_id: str, new_name: str) -> Dict:
    """
    Rename a video in Drive and write-through the catalog + snapshot publish.
    """
    result = await run_blocking(
        drive_manager.rename_file,
        file_id,
        new_name,
        semaphore=get_drive_semaphore(),
        label="drive.rename",
    )
    if settings.CATALOG_ENABLED and result.get("status") == "success":
        try:
            new_file_name = result.get("new_name")
            if new_file_name:
                await rename_drive_video_in_catalog(
                    video_file_id=file_id,
                    new_file_name=str(new_file_name),
                )
                await maybe_publish_drive_snapshot(reason="drive_rename")
        except Exception as e:
            logger.warning(f"Catalog write-through failed (drive_rename): {e}")
    return result


async def update_drive_thumbnail(file_id: str, thumbnail_data: bytes, file_ext: str) -> Dict:
    """
    Update a Drive thumbnail and write-through the catalog + snapshot publish.
    """
    result = await run_blocking(
        drive_manager.update_thumbnail,
        file_id,
        thumbnail_data,
        file_ext,
        semaphore=get_drive_semaphore(),
        label="drive.update_thumbnail",
    )
    if settings.CATALOG_ENABLED and result.get("status") == "success":
        thumbnail_id = result.get("thumbnail_id")
        if thumbnail_id:
            try:
                await set_drive_thumbnail_in_catalog(
                    video_file_id=file_id,
                    thumbnail_file_id=str(thumbnail_id),
                )
                await maybe_publish_drive_snapshot(reason="drive_update_thumbnail")
            except Exception as e:
                logger.warning(f"Catalog write-through failed (drive_update_thumbnail): {e}")
    return result


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

        # Sync uploaded videos to cache
        uploaded_files = result.get("uploaded", [])
        for uploaded_file in uploaded_files:
            if uploaded_file.get("status") == "success":
                file_name = uploaded_file.get("name", "")
                # Only sync video files (not thumbnails, subtitles, etc.)
                if any(file_name.lower().endswith(ext) for ext in settings.VIDEO_EXTENSIONS):
                    try:
                        from .cache import sync_video_added
                        video_path = f"{folder_name}/{file_name}"
                        await sync_video_added(
                            drive_id=uploaded_file.get("file_id"),
                            name=file_name,
                            path=video_path,
                            size=uploaded_file.get("size", 0),
                            created_at=datetime.now().isoformat(),
                            modified_at=datetime.now().isoformat(),
                        )
                        logger.info(f"Synced video to cache: {video_path}")
                    except Exception as cache_err:
                        logger.warning(f"Failed to sync video to cache: {cache_err}")

        if settings.CATALOG_ENABLED:
            try:
                by_base: Dict[str, List[Dict]] = {}

                def base_key(name: str) -> str:
                    lower = name.lower()
                    if lower.endswith(".info.json"):
                        return name[:-len(".info.json")]
                    if lower.endswith(".description"):
                        return name[:-len(".description")]
                    return Path(name).stem

                for item in uploaded_files:
                    if item.get("status") not in {"success", "skipped"}:
                        continue
                    file_name = item.get("name")
                    file_id = item.get("file_id")
                    if not file_name or not file_id:
                        continue
                    key = base_key(str(file_name))
                    by_base.setdefault(key, []).append(item)

                for items in by_base.values():
                    video_item = next(
                        (
                            it
                            for it in items
                            if it.get("name")
                            and any(
                                str(it["name"]).lower().endswith(ext)
                                for ext in settings.VIDEO_EXTENSIONS
                            )
                        ),
                        None,
                    )
                    if not video_item:
                        continue
                    video_name = str(video_item["name"])
                    drive_path = f"{folder_name}/{video_name}"

                    related = [
                        {"name": it.get("name"), "file_id": it.get("file_id")}
                        for it in items
                        if it is not video_item
                    ]

                    await upsert_drive_video_from_upload(
                        video_file_id=str(video_item.get("file_id")),
                        drive_path=drive_path,
                        size_bytes=int(video_item.get("size") or 0),
                        related_files=related,
                    )

                await maybe_publish_drive_snapshot(reason="drive_upload_external")
            except Exception as e:
                logger.warning(f"Catalog write-through failed (drive_upload_external): {e}")

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
            if settings.CATALOG_ENABLED and result.get("status") == "success":
                try:
                    out_dir = Path(base_dir).resolve()
                    video_abs = Path(result.get("path") or "").resolve()
                    if video_abs.exists() and any(
                        str(video_abs).lower().endswith(ext) for ext in settings.VIDEO_EXTENSIONS
                    ):
                        video_rel = video_abs.relative_to(out_dir).as_posix()
                        thumb_rel = None
                        for ext in settings.THUMBNAIL_EXTENSIONS:
                            candidate = video_abs.with_suffix(ext)
                            if candidate.exists():
                                thumb_rel = candidate.relative_to(out_dir).as_posix()
                                break

                        await upsert_local_video_from_fs(
                            video_path=video_rel,
                            base_dir=str(out_dir),
                            thumbnail_path=thumb_rel,
                        )
                except Exception as e:
                    logger.warning(f"Catalog write-through failed (drive_download_single): {e}")

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
        if settings.CATALOG_ENABLED:
            repo = CatalogRepository()
            counts = await run_blocking(
                repo.get_counts,
                semaphore=get_catalog_semaphore(),
                label="drive.download.counts",
            )
            drive_state = await run_blocking(
                repo.get_state,
                "drive",
                semaphore=get_catalog_semaphore(),
                label="drive.download.state",
            )
            drive_imported = bool(drive_state.get("last_imported_at"))
            if counts.get("drive", 0) == 0 and not drive_imported:
                raise Exception("Catálogo do Drive vazio: rode /api/catalog/drive/import ou /api/catalog/drive/rebuild antes de baixar.")

            local_set, drive_map = await run_blocking(
                _get_catalog_sets,
                repo,
                semaphore=get_catalog_semaphore(),
                label="drive.download.sets",
            )
            drive_set = set(drive_map.keys())
            drive_only_items = [(p, drive_map[p]) for p in sorted(drive_set - local_set) if drive_map.get(p)]
        else:
            sync_state = await run_blocking(
                drive_manager.get_sync_state,
                base_dir,
                semaphore=get_drive_semaphore(),
                label="drive.download.sync_state",
            )
            drive_only_items = []
            for p in sync_state["drive_only"]:
                v = await run_blocking(
                    drive_manager.get_video_by_path,
                    p,
                    semaphore=get_drive_semaphore(),
                    label="drive.download.by_path",
                )
                if v:
                    drive_only_items.append((p, v["id"]))

        total = len(drive_only_items)

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

        # Contadores thread-safe
        results = {"downloaded": 0, "failed": [], "files": []}
        results_lock = asyncio.Lock()
        files_in_progress: List[str] = []
        progress_lock = asyncio.Lock()

        semaphore = _get_download_semaphore()

        async def download_with_semaphore(video_path: str, file_id: str) -> None:
            """Download um arquivo com controle de concorrência."""
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
                    # Download usando thread para não bloquear event loop
                    result = await asyncio.to_thread(
                        drive_manager.download_file,
                        file_id,
                        video_path,
                        base_dir,
                        None  # No progress callback for batch
                    )

                    if settings.CATALOG_ENABLED and result.get("status") != "error":
                        try:
                            out_dir = Path(base_dir).resolve()
                            video_abs = Path(result.get("path") or "").resolve()
                            if (
                                video_abs.exists()
                                and video_abs.suffix.lower() in settings.VIDEO_EXTENSIONS
                            ):
                                video_rel = video_abs.relative_to(out_dir).as_posix()
                                thumb_rel = None
                                for ext in settings.THUMBNAIL_EXTENSIONS:
                                    candidate = video_abs.with_suffix(ext)
                                    if candidate.exists():
                                        thumb_rel = candidate.relative_to(out_dir).as_posix()
                                        break

                                await upsert_local_video_from_fs(
                                    video_path=video_rel,
                                    base_dir=str(out_dir),
                                    thumbnail_path=thumb_rel,
                                )
                        except Exception as e:
                            logger.warning(f"Catalog write-through failed (drive_download_batch): {e}")

                    async with results_lock:
                        results["downloaded"] += 1
                        results["files"].append(result)

                except Exception as e:
                    async with results_lock:
                        results["failed"].append({
                            "file": video_path,
                            "error": str(e)
                        })
                finally:
                    in_progress_snapshot: List[str]
                    async with progress_lock:
                        if video_path in files_in_progress:
                            files_in_progress.remove(video_path)
                        in_progress_snapshot = files_in_progress.copy()

                    async with results_lock:
                        done = results["downloaded"] + len(results["failed"])
                        _update_download_progress(job_id, {
                            "status": "downloading",
                            "total": total,
                            "downloaded": results["downloaded"],
                            "failed": len(results["failed"]),
                            "percent": (done / total) * 100,
                            "current_file": None,
                            "files_in_progress": in_progress_snapshot
                        })

        # Criar todas as tasks (semaphore controla concorrência)
        tasks = [
            download_with_semaphore(video_path, file_id)
            for (video_path, file_id) in drive_only_items
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

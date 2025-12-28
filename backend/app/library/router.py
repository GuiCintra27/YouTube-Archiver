"""
Library router - API endpoints for local video library.

Provides endpoints for:
- Listing downloaded videos with pagination
- Streaming videos with Range Request support
- Serving thumbnails
- Deleting videos and related files
"""
import asyncio
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, Response

from app.core.logging import get_module_logger
from app.core.rate_limit import limiter, RateLimits
from typing import List
from fastapi import UploadFile, File, Form
from pydantic import BaseModel
from .service import get_paginated_videos, delete_video_with_related, delete_videos_batch, rename_video, update_video_thumbnail
from app.catalog.service import (
    list_local_videos_paginated,
    delete_local_video_from_catalog,
    rename_local_video_in_catalog,
    upsert_local_video_from_fs,
)
from app.core.blocking import run_blocking, get_fs_semaphore


class RenameRequest(BaseModel):
    new_name: str
from app.config import settings
from app.core.security import sanitize_path, validate_path_within_base, validate_file_exists, encode_filename_for_header
from app.core.exceptions import (
    VideoNotFoundException,
    ThumbnailNotFoundException,
    InvalidRequestException,
    InvalidRangeHeaderException,
    RangeNotSatisfiableException,
)

logger = get_module_logger("library")

router = APIRouter(prefix="/api/videos", tags=["library"])


@router.get(
    "",
    summary="Listar vídeos da biblioteca",
    description="""
Lista os vídeos baixados na biblioteca local.

**Estrutura de diretórios:**
Os vídeos são organizados em `downloads/[canal]/[subcategoria]/video.mp4`.

**Paginação:**
- `page`: Número da página (começa em 1)
- `limit`: Itens por página (opcional, retorna todos se omitido)

**Resposta:**
Inclui metadados de cada vídeo: título, canal, tamanho, data de criação,
caminho relativo e thumbnail se disponível.

**Cache:**
Os resultados são cacheados por 30 segundos para melhor performance.
    """,
    responses={
        200: {
            "description": "Lista paginada de vídeos",
            "content": {
                "application/json": {
                    "example": {
                        "total": 150,
                        "page": 1,
                        "limit": 24,
                        "videos": [
                            {
                                "id": "Channel/video.mp4",
                                "title": "Video Title",
                                "channel": "Channel",
                                "path": "Channel/video.mp4",
                                "thumbnail": "Channel/video.jpg",
                                "size": 104857600,
                                "created_at": "2024-01-15T10:30:00",
                                "modified_at": "2024-01-15T10:30:00"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Parâmetros de paginação inválidos"},
    }
)
@limiter.limit(RateLimits.LIST_VIDEOS)
async def list_videos(request: Request, base_dir: str = "./downloads", page: int = 1, limit: Optional[int] = None):
    """Lista vídeos disponíveis na biblioteca (com paginação opcional)."""
    if page < 1:
        raise InvalidRequestException("Página deve ser >= 1")
    if limit is not None and limit <= 0:
        raise InvalidRequestException("Limite deve ser > 0")

    if settings.CATALOG_ENABLED:
        effective_limit = limit if limit is not None else 1000000
        return await list_local_videos_paginated(page=page, limit=effective_limit)

    return await run_blocking(
        get_paginated_videos,
        base_dir,
        page,
        limit,
        semaphore=get_fs_semaphore(),
        label="library.list_videos",
    )


@router.get(
    "/stream/{video_path:path}",
    summary="Stream de vídeo",
    description="""
Serve o arquivo de vídeo para reprodução no navegador.

**Range Requests (HTTP 206):**
Suporta Range Requests para permitir seek/skip no player.
O navegador pode solicitar partes específicas do arquivo.

**Formatos suportados:**
MP4, WebM, MKV, AVI, MOV e outros formatos de vídeo comuns.

**Headers importantes:**
- `Accept-Ranges: bytes` - indica suporte a range requests
- `Content-Range` - indica o range sendo servido
- `Content-Disposition` - nome do arquivo com encoding UTF-8
    """,
    responses={
        200: {"description": "Arquivo de vídeo completo"},
        206: {"description": "Conteúdo parcial (range request)"},
        404: {"description": "Vídeo não encontrado"},
        416: {"description": "Range não satisfatório"},
    }
)
@limiter.limit(RateLimits.STREAM_VIDEO)
async def stream_video(request: Request, video_path: str, base_dir: str = "./downloads"):
    """Serve o arquivo de vídeo para streaming com suporte a Range Requests."""
    try:
        # Sanitize and validate path
        video_path = sanitize_path(video_path)
        full_path = Path(base_dir) / video_path
        base_path = Path(base_dir)

        logger.debug(f"Streaming video: {video_path}")
        logger.debug(f"Full path: {full_path}")

        validate_file_exists(full_path)
        validate_path_within_base(full_path, base_path)

        # Detect MIME type
        file_ext = full_path.suffix.lower()
        media_type = settings.VIDEO_MIME_TYPES.get(file_ext, 'video/mp4')

        file_size = full_path.stat().st_size
        logger.debug(f"Media type: {media_type}, File size: {file_size}")

        # Check for range request
        range_header = request.headers.get("range")

        if not range_header:
            # Full response without range (streamed to avoid threadpool FileResponse)
            start = 0
            end = file_size - 1
            chunk_size = file_size

            async def iterfile():
                with open(full_path, 'rb') as f:
                    while True:
                        data = f.read(8192)
                        if not data:
                            break
                        yield data
                        await asyncio.sleep(0)

            encoded_filename = encode_filename_for_header(full_path.name)
            headers = {
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
            }

            return StreamingResponse(
                iterfile(),
                status_code=200,
                media_type=media_type,
                headers=headers,
            )

        # Process range request
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

        if not range_match:
            raise InvalidRangeHeaderException()

        start = int(range_match.group(1))
        end = int(range_match.group(2)) if range_match.group(2) else file_size - 1

        if start >= file_size or end >= file_size or start > end:
            raise RangeNotSatisfiableException()

        chunk_size = end - start + 1

        async def iterfile():
            with open(full_path, 'rb') as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    read_size = min(8192, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
                    await asyncio.sleep(0)

        encoded_filename = encode_filename_for_header(full_path.name)
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
        }

        return StreamingResponse(
            iterfile(),
            status_code=206,
            media_type=media_type,
            headers=headers
        )

    except (VideoNotFoundException, InvalidRangeHeaderException, RangeNotSatisfiableException):
        raise
    except Exception as e:
        logger.error(f"Exception in stream_video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/thumbnail/{thumbnail_path:path}",
    summary="Obter thumbnail",
    description="""
Serve a thumbnail (miniatura) de um vídeo.

**Formatos suportados:**
JPG, JPEG, PNG, WebP

**Cache:**
Retorna headers de cache para otimizar carregamento.
    """,
    responses={
        200: {"description": "Imagem da thumbnail"},
        404: {"description": "Thumbnail não encontrada"},
    }
)
@limiter.limit(RateLimits.DEFAULT)
async def get_thumbnail(request: Request, thumbnail_path: str, base_dir: str = "./downloads"):
    """Serve a thumbnail do vídeo."""
    try:
        thumbnail_path = sanitize_path(thumbnail_path)
        full_path = Path(base_dir) / thumbnail_path
        base_path = Path(base_dir)

        if not full_path.exists() or not full_path.is_file():
            raise ThumbnailNotFoundException()

        validate_path_within_base(full_path, base_path)

        media_type = settings.IMAGE_MIME_TYPES.get(full_path.suffix.lower(), 'image/jpeg')

        content = await run_blocking(
            full_path.read_bytes,
            semaphore=get_fs_semaphore(),
            label="library.thumbnail",
        )
        return Response(content=content, media_type=media_type)

    except ThumbnailNotFoundException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/delete-batch",
    summary="Excluir múltiplos vídeos",
    description="""
Exclui múltiplos vídeos e todos os arquivos associados de uma só vez.

**Limite:** Máximo de 100 vídeos por requisição.

**Arquivos removidos para cada vídeo:**
- Arquivo de vídeo principal
- Thumbnail (se existir)
- Legendas (.srt, .vtt)
- Metadados (.info.json, .description)

**Atenção:** Esta ação não pode ser desfeita.
    """,
    responses={
        200: {
            "description": "Resultado da exclusão em lote",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "5 vídeo(s) excluído(s)",
                        "total_deleted": 5,
                        "total_failed": 0
                    }
                }
            }
        },
        400: {"description": "Requisição inválida"},
    }
)
@limiter.limit(RateLimits.DELETE)
async def delete_videos_batch_endpoint(request: Request, video_paths: List[str], base_dir: str = "./downloads"):
    """Exclui múltiplos vídeos e seus arquivos associados."""
    try:
        if not video_paths:
            raise InvalidRequestException("video_paths list cannot be empty")

        if len(video_paths) > 100:
            raise InvalidRequestException("Cannot delete more than 100 videos at once")

        result = await run_blocking(
            delete_videos_batch,
            video_paths,
            base_dir,
            semaphore=get_fs_semaphore(),
            label="library.delete_batch",
        )
        for item in result.get("deleted", []):
            await delete_local_video_from_catalog(video_path=sanitize_path(item.get("path", "")))
        return result
    except InvalidRequestException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/rename/{video_path:path}",
    summary="Renomear vídeo",
    description="""
Renomeia um vídeo e todos os arquivos associados.

**Arquivos renomeados:**
- Arquivo de vídeo principal
- Thumbnail (se existir)
- Legendas (.srt, .vtt)
- Metadados (.info.json, .description)

**Validação:**
- O novo nome não pode estar vazio
- Caracteres inválidos são removidos automaticamente
    """,
    responses={
        200: {
            "description": "Vídeo renomeado com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Vídeo renomeado com sucesso",
                        "new_path": "Channel/New Name.mp4",
                        "renamed_files": [
                            {"old": "Channel/Old Name.mp4", "new": "Channel/New Name.mp4"}
                        ]
                    }
                }
            }
        },
        404: {"description": "Vídeo não encontrado"},
        400: {"description": "Nome inválido"},
    }
)
@limiter.limit(RateLimits.DEFAULT)
async def rename_video_endpoint(request: Request, video_path: str, body: RenameRequest, base_dir: str = "./downloads"):
    """Renomeia um vídeo e seus arquivos associados."""
    try:
        result = await run_blocking(
            rename_video,
            video_path,
            body.new_name,
            base_dir,
            semaphore=get_fs_semaphore(),
            label="library.rename",
        )
        new_path = result.get("new_path")
        if new_path:
            # Try to detect new thumbnail path from renamed files
            new_thumb = None
            for item in result.get("renamed_files", []):
                new_file = item.get("new")
                if isinstance(new_file, str) and Path(new_file).suffix.lower() in settings.THUMBNAIL_EXTENSIONS:
                    new_thumb = new_file
                    break
            await rename_local_video_in_catalog(
                old_video_path=sanitize_path(video_path),
                new_video_path=new_path,
                base_dir=base_dir,
                new_thumbnail_path=new_thumb,
            )
        return result
    except ValueError as e:
        raise InvalidRequestException(str(e))
    except (VideoNotFoundException,):
        raise
    except Exception as e:
        logger.error(f"Error renaming video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/update-thumbnail/{video_path:path}",
    summary="Atualizar thumbnail",
    description="""
Atualiza a thumbnail (miniatura) de um vídeo.

**Formatos suportados:**
JPG, JPEG, PNG, WebP

**Comportamento:**
- Remove thumbnails antigas automaticamente
- Salva a nova thumbnail com o mesmo nome base do vídeo
    """,
    responses={
        200: {
            "description": "Thumbnail atualizada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Thumbnail atualizada com sucesso",
                        "thumbnail_path": "Channel/video.jpg"
                    }
                }
            }
        },
        404: {"description": "Vídeo não encontrado"},
        400: {"description": "Formato de imagem inválido"},
    }
)
@limiter.limit(RateLimits.DEFAULT)
async def update_thumbnail_endpoint(
    request: Request,
    video_path: str,
    thumbnail: UploadFile = File(...),
    base_dir: str = "./downloads"
):
    """Atualiza a thumbnail de um vídeo."""
    try:
        # Get file extension from uploaded file
        if not thumbnail.filename:
            raise InvalidRequestException("Thumbnail filename is required")

        file_ext = Path(thumbnail.filename).suffix.lower()
        if file_ext not in settings.THUMBNAIL_EXTENSIONS:
            raise InvalidRequestException(f"Invalid image format: {file_ext}. Supported: {', '.join(settings.THUMBNAIL_EXTENSIONS)}")

        # Read file content
        thumbnail_data = await thumbnail.read()

        result = await run_blocking(
            update_video_thumbnail,
            video_path,
            thumbnail_data,
            file_ext,
            base_dir,
            semaphore=get_fs_semaphore(),
            label="library.update_thumbnail",
        )
        thumb_path = result.get("thumbnail_path")
        if thumb_path:
            await upsert_local_video_from_fs(
                video_path=sanitize_path(video_path),
                base_dir=base_dir,
                thumbnail_path=thumb_path,
            )
        return result
    except InvalidRequestException:
        raise
    except ValueError as e:
        raise InvalidRequestException(str(e))
    except (VideoNotFoundException,):
        raise
    except Exception as e:
        logger.error(f"Error updating thumbnail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/{video_path:path}",
    summary="Excluir vídeo",
    description="""
Exclui um vídeo e todos os arquivos associados.

**Arquivos removidos:**
- Arquivo de vídeo principal
- Thumbnail (se existir)
- Legendas (.srt, .vtt)
- Metadados (.info.json, .description)

**Limpeza adicional:**
- Remove entrada do arquivo de archive (evita re-download)
- Remove diretórios vazios após exclusão

**Atenção:** Esta ação não pode ser desfeita.
    """,
    responses={
        200: {
            "description": "Vídeo excluído com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Vídeo excluído com sucesso",
                        "deleted_files": ["Channel/video.mp4", "Channel/video.jpg"],
                        "removed_from_archive": True
                    }
                }
            }
        },
        404: {"description": "Vídeo não encontrado"},
    }
)
@limiter.limit(RateLimits.DELETE)
async def delete_video(request: Request, video_path: str, base_dir: str = "./downloads"):
    """Exclui um vídeo e seus arquivos associados."""
    try:
        result = await run_blocking(
            delete_video_with_related,
            video_path,
            base_dir,
            semaphore=get_fs_semaphore(),
            label="library.delete_video",
        )
        await delete_local_video_from_catalog(video_path=sanitize_path(video_path))
        return result
    except (VideoNotFoundException,):
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

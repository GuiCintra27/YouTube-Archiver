"""
Módulo para gerenciar downloads usando yt-dlp.
Versão standalone para uso na API, sem dependências do main.py.
"""
from __future__ import annotations
import os
import time
import random
import pathlib
import threading
import urllib.parse as urlparse
from dataclasses import dataclass
from typing import Optional, Callable
from yt_dlp import YoutubeDL


DEFAULT_TEMPLATE = os.path.join(
    "{out}",
    "%(uploader|Unknown)s",
    "%(playlist_title|NoPlaylist)s",
    "%(upload_date>%Y-%m-%d|0000-00-00)s - %(title).180B [%(id)s].%(ext)s",
)

MEDIA_EXTS = {".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".mov"}


@dataclass
class Settings:
    """Configurações de download"""
    out_dir: str
    archive_file: str
    fmt: str = "bv*+ba/b"
    max_res: Optional[int] = None
    subs: bool = True
    auto_subs: bool = True
    sub_langs: str = "pt,en"
    thumbnails: bool = True
    audio_only: bool = False
    workers: int = 1
    limit: Optional[int] = None
    dry_run: bool = False
    # drive
    drive_upload: bool = False
    drive_root: str = "YouTubeArchive"
    drive_credentials: str = "./credentials.json"
    drive_token: str = "./token.json"
    uploaded_log: str = "./uploaded.jsonl"
    cookies_file: Optional[str] = None
    referer: Optional[str] = None
    origin: Optional[str] = None
    user_agent: str = "yt-archiver"
    concurrent_fragments: int = 10
    custom_path: Optional[str] = None
    file_name: Optional[str] = None
    archive_id: Optional[str] = None
    # Rate limiting (anti-ban)
    delay_between_downloads: int = 0  # Segundos entre cada vídeo
    batch_size: Optional[int] = None  # Tamanho do batch (0 = sem batches)
    batch_delay: int = 0  # Segundos entre batches
    randomize_delay: bool = False  # Randomizar delays para parecer humano


def _build_format(fmt: str, max_res: Optional[int]) -> str:
    """Constrói string de formato para yt-dlp"""
    if max_res:
        return f"bestvideo[height<={max_res}]+bestaudio/best[height<={max_res}]"
    return fmt


def _outtmpl(s: Settings) -> str:
    """Gera template de saída para yt-dlp"""
    if s.custom_path or s.file_name:
        base_dir = (
            os.path.join(s.out_dir, s.custom_path) if s.custom_path else s.out_dir
        )
        name_tmpl = (
            (s.file_name.strip() + ".%(ext)s")
            if s.file_name
            else "%(upload_date>%Y-%m-%d|0000-00-00)s - %(title).180B [%(id)s].%(ext)s"
        )
        return os.path.join(base_dir, name_tmpl)
    return DEFAULT_TEMPLATE.format(out=s.out_dir)


def _base_opts(s: Settings) -> dict:
    """Configurações base do yt-dlp"""
    postprocessors = []
    if s.audio_only:
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }
        )

    # Headers dinâmicos
    headers = {"User-Agent": s.user_agent}
    if s.referer:
        headers["Referer"] = s.referer
    if s.origin:
        headers["Origin"] = s.origin

    ydl_opts = {
        "format": _build_format(s.fmt, s.max_res),
        "outtmpl": _outtmpl(s),
        "writethumbnail": s.thumbnails,
        "writesubtitles": s.subs,
        "writeautomaticsub": s.auto_subs,
        "subtitleslangs": [l.strip() for l in s.sub_langs.split(",") if l.strip()],
        "merge_output_format": None,
        "postprocessors": postprocessors,
        "ignoreerrors": True,
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": s.concurrent_fragments,
        "http_headers": headers,
        "noprogress": True,
        "download_archive": None if s.archive_id else s.archive_file,
        "geo_bypass": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": s.dry_run,
        "writeinfojson": True,
    }

    # Cookies opcionais
    if s.cookies_file:
        ydl_opts["cookiefile"] = s.cookies_file

    return ydl_opts


def _extract_entries(url: str, limit: Optional[int]) -> list[str]:
    """Extrai URLs de uma playlist ou retorna URL única"""
    with YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    urls: list[str] = []
    if not info:
        return urls

    if info.get("_type") == "playlist":
        entries = info.get("entries") or []
        for e in entries[: limit or len(entries)]:
            vid = e.get("url") or e.get("id")
            if vid:
                urls.append(
                    f"https://www.youtube.com/watch?v={vid}" if len(vid) == 11 else vid
                )
    else:
        urls.append(info.get("webpage_url") or url)

    if limit and len(urls) > limit:
        urls = urls[:limit]

    return urls


def _custom_archive_has(path: str, key: str) -> bool:
    """Verifica se uma entrada existe no arquivo de archive customizado"""
    if not key or not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return any(ln.strip() == f"custom {key}" for ln in f)
    except Exception:
        return False


def _custom_archive_add(path: str, key: str) -> None:
    """Adiciona uma entrada ao arquivo de archive customizado"""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"custom {key}\n")
    except Exception:
        pass


class DownloadProgress:
    """Callback otimizado para capturar progresso do download"""

    def __init__(self, on_progress: Optional[Callable] = None):
        self.on_progress = on_progress
        self.current_file = ""
        self.total_files = 0
        self.current_index = 0

        # Throttling: só atualizar a cada X%
        self.last_percentage = 0
        self.update_threshold = 2  # Atualizar a cada 2% de mudança

    def __call__(self, d):
        if not self.on_progress:
            return

        status = d.get("status")

        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)

            # Calcular porcentagem apenas uma vez
            if total > 0:
                percentage = (downloaded / total * 100)

                # Throttling: só atualizar se mudou significativamente
                if abs(percentage - self.last_percentage) < self.update_threshold:
                    return  # Pular este update

                self.last_percentage = percentage
            else:
                percentage = 0

            # Cache do basename (evita chamar toda vez)
            filename = d.get("filename", "")

            progress_data = {
                "status": "downloading",
                "filename": os.path.basename(filename) if filename else "",
                "filepath": filename,
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "speed": d.get("speed", 0),
                "eta": d.get("eta", 0),
                "percentage": percentage,
                "current_file": self.current_index,
                "total_files": self.total_files,
            }
            self.on_progress(progress_data)

        elif status == "finished":
            # Sempre reportar finished
            self.last_percentage = 100
            self.on_progress({
                "status": "finished",
                "filename": os.path.basename(d.get("filename", "")),
                "filepath": d.get("filename", ""),
            })


def download_video(
    url: str,
    settings: Settings,
    on_progress: Optional[Callable] = None,
) -> dict:
    """
    Baixa um vídeo e retorna informações sobre o download.

    Args:
        url: URL do vídeo/playlist
        settings: Configurações de download
        on_progress: Callback para progresso (opcional)

    Returns:
        Dict com informações do download
    """
    try:
        # Configurar callback de progresso
        progress_callback = DownloadProgress(on_progress)

        # Configurar opções do yt-dlp
        opts = _base_opts(settings)
        opts["progress_hooks"] = [progress_callback]

        # Extrair informações antes de baixar
        urls = _extract_entries(url, settings.limit)
        progress_callback.total_files = len(urls)

        results = []

        for idx, video_url in enumerate(urls):
            progress_callback.current_index = idx + 1

            # Verificar se já foi baixado
            if settings.archive_id and _custom_archive_has(settings.archive_file, settings.archive_id):
                results.append({
                    "url": video_url,
                    "status": "skipped",
                    "message": "Already downloaded (archive)",
                })
                continue

            # Baixar
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(video_url, download=True)

                if info:
                    results.append({
                        "url": video_url,
                        "status": "success",
                        "title": info.get("title"),
                        "id": info.get("id"),
                        "duration": info.get("duration"),
                    })

                    # Adicionar ao arquivo de archive
                    if settings.archive_id:
                        _custom_archive_add(settings.archive_file, settings.archive_id)

            # === ANTI-BAN: Delays entre downloads ===
            # Só aplicar delay se não for o último vídeo
            if idx < len(urls) - 1:
                # Delay entre vídeos
                if settings.delay_between_downloads > 0:
                    delay = settings.delay_between_downloads

                    # Randomizar delay para parecer humano
                    if settings.randomize_delay:
                        # Varia entre 80% e 120% do delay configurado
                        delay = delay * random.uniform(0.8, 1.2)

                    if on_progress:
                        on_progress({
                            "status": "waiting",
                            "message": f"Aguardando {int(delay)}s antes do próximo vídeo...",
                            "delay_remaining": int(delay),
                        })

                    time.sleep(delay)

                # Delay entre batches (grupos de vídeos)
                if settings.batch_size and settings.batch_delay > 0:
                    # Verificar se completou um batch
                    videos_downloaded = idx + 1
                    if videos_downloaded % settings.batch_size == 0:
                        batch_delay = settings.batch_delay

                        if settings.randomize_delay:
                            batch_delay = batch_delay * random.uniform(0.9, 1.1)

                        if on_progress:
                            on_progress({
                                "status": "batch_waiting",
                                "message": f"Pausa entre batches: {int(batch_delay)}s...",
                                "delay_remaining": int(batch_delay),
                                "batch_completed": videos_downloaded // settings.batch_size,
                            })

                        time.sleep(batch_delay)

        return {
            "status": "completed",
            "results": results,
            "total": len(results),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


def get_video_info(url: str) -> dict:
    """
    Obtém informações sobre um vídeo sem baixar.

    Args:
        url: URL do vídeo

    Returns:
        Dict com informações do vídeo
    """
    try:
        with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                return {"status": "error", "error": "No info found"}

            # Se for playlist, retornar info da playlist
            if info.get("_type") == "playlist":
                entries = info.get("entries", [])
                return {
                    "status": "success",
                    "type": "playlist",
                    "title": info.get("title"),
                    "uploader": info.get("uploader"),
                    "video_count": len(entries),
                    "videos": [
                        {
                            "title": e.get("title"),
                            "id": e.get("id"),
                            "duration": e.get("duration"),
                        }
                        for e in entries[:10]  # Primeiros 10
                    ],
                }
            else:
                # Vídeo individual
                return {
                    "status": "success",
                    "type": "video",
                    "title": info.get("title"),
                    "uploader": info.get("uploader"),
                    "duration": info.get("duration"),
                    "view_count": info.get("view_count"),
                    "thumbnail": info.get("thumbnail"),
                }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }

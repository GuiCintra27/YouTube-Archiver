from __future__ import annotations
import os, sys, json, pathlib, concurrent.futures, typing as t
from dataclasses import dataclass
import threading
import urllib.parse as urlparse
import typer
from rich import print
from rich.console import Console
from rich.progress import track
from yt_dlp import YoutubeDL

# ---- Google Drive API ----
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

app = typer.Typer(
    help="Archive public YouTube content (channel/playlist/urls) with optional Google Drive upload"
)
console = Console()

DEFAULT_TEMPLATE = os.path.join(
    "{out}",
    "%(uploader|Unknown)s",
    "%(playlist_title|NoPlaylist)s",
    "%(upload_date>%Y-%m-%d|0000-00-00)s - %(title).180B [%(id)s].%(ext)s",
)

MEDIA_EXTS = {".mp4", ".mkv", ".webm", ".mp3", ".m4a", ".mov"}


@dataclass
class Settings:
    out_dir: str
    archive_file: str
    fmt: str = "bv*+ba/b"
    max_res: t.Optional[int] = None
    subs: bool = True
    auto_subs: bool = True
    sub_langs: str = "pt,en"
    thumbnails: bool = True
    audio_only: bool = False
    workers: int = 1
    limit: t.Optional[int] = None
    dry_run: bool = False
    # drive
    drive_upload: bool = False
    drive_root: str = "YouTubeArchive"
    drive_credentials: str = "./credentials.json"
    drive_token: str = "./token.json"
    uploaded_log: str = "./uploaded.jsonl"
    cookies_file: t.Optional[str] = None
    referer: t.Optional[str] = None
    origin: t.Optional[str] = None
    user_agent: str = "yt-archiver"
    concurrent_fragments: int = 10
    custom_path: t.Optional[str] = None
    file_name: t.Optional[str] = None
    archive_id: t.Optional[str] = None


# ---------------- Google Drive helpers -----------------
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class DriveClient:
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._lock = threading.Lock()
        self._service = None

    def _get_service(self):
        with self._lock:
            if self._service is not None:
                return self._service
            creds = None
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(
                            f"Missing credentials file: {self.credentials_path}"
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())
            self._service = build("drive", "v3", credentials=creds)
            return self._service

    def ensure_folder(self, name: str, parent_id: str | None) -> str:
        svc = self._get_service()
        q = [
            "mimeType = 'application/vnd.google-apps.folder'",
            "trashed = false",
            f"name = '{name.replace("'","\'")}'",
        ]
        if parent_id:
            q.append(f"'{parent_id}' in parents")
        res = svc.files().list(q=" and ".join(q), fields="files(id,name)").execute()
        files = res.get("files", [])
        if files:
            return files[0]["id"]
        meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_id:
            meta["parents"] = [parent_id]
        folder = svc.files().create(body=meta, fields="id").execute()
        return folder["id"]

    def ensure_path(self, parts: list[str]) -> str:
        parent = None
        for part in parts:
            parent = self.ensure_folder(part, parent)
        return parent  # final folder id

    def upload_file(self, local_path: str, parent_id: str) -> str:
        svc = self._get_service()
        mime = None  # let Drive infer
        media = MediaFileUpload(
            local_path, mimetype=mime, chunksize=8 * 1024 * 1024, resumable=True
        )
        body = {"name": os.path.basename(local_path), "parents": [parent_id]}
        file = svc.files().create(body=body, media_body=media, fields="id").execute()
        return file["id"]


class UploadLog:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()
        self._ids: set[str] = set()
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if "video_id" in obj:
                            self._ids.add(obj["video_id"])
                    except Exception:
                        pass

    def has(self, vid: str) -> bool:
        return vid in self._ids

    def add(self, vid: str, local_path: str, drive_id: str):
        with self._lock:
            with open(self.path, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "video_id": vid,
                            "local_path": local_path,
                            "drive_file_id": drive_id,
                        }
                    )
                    + ""
                )
            self._ids.add(vid)


# ---------------- yt-dlp helpers -----------------


def _build_format(fmt: str, max_res: t.Optional[int]) -> str:
    if max_res:
        return f"bestvideo[height<={max_res}]+bestaudio/best[height<={max_res}]"
    return fmt


def _outtmpl(s: Settings) -> str:
    # Se usuário passou path/nome custom, usamos isso.
    if s.custom_path or s.file_name:
        base_dir = (
            os.path.join(s.out_dir, s.custom_path) if s.custom_path else s.out_dir
        )
        # Mantive "[%(id)s]" no nome para garantir unicidade e não quebrar o upload pro Drive.
        # Se quiser exatamente "Aula 01.ext", é só tirar " [%(id)s]" desta linha.
        name_tmpl = (
            (s.file_name.strip() + ".%(ext)s")
            if s.file_name
            else "%(upload_date>%Y-%m-%d|0000-00-00)s - %(title).180B [%(id)s].%(ext)s"
        )
        return os.path.join(base_dir, name_tmpl)
    # Caso contrário, segue o padrão antigo
    return DEFAULT_TEMPLATE.format(out=s.out_dir)


def _base_opts(s: Settings) -> dict:
    postprocessors = []
    if s.audio_only:
        postprocessors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }
        )
    # (sem remux para mp4 quando NÃO é audio_only)

    # >>> ADIÇÃO: headers dinâmicos
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
        # >>> ALTERAR para usar o valor vindo da CLI
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

    # >>> ADIÇÃO: cookies opcionais
    if s.cookies_file:
        ydl_opts["cookiefile"] = s.cookies_file

    return ydl_opts


def _extract_entries(url: str, limit: t.Optional[int]) -> list[str]:
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


def _resolve_input(source: str) -> list[str]:
    p = pathlib.Path(source)
    if p.exists() and p.is_file():
        lines = [
            ln.strip()
            for ln in p.read_text().splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        return lines
    return [source]


def _video_id_from_url(url: str) -> str | None:
    try:
        u = urlparse.urlparse(url)
        if u.netloc.endswith("youtu.be"):
            vid = u.path.strip("/")
            return vid or None
        if "watch" in u.path:
            q = urlparse.parse_qs(u.query)
            if "v" in q:
                return q["v"][0]
    except Exception:
        return None
    return None


def _find_media_by_id(out_dir: str, vid: str) -> str | None:
    out_dir = os.path.abspath(out_dir)
    for root, _, files in os.walk(out_dir):
        for f in files:
            ext = pathlib.Path(f).suffix.lower()
            if ext not in MEDIA_EXTS:
                continue
            # our template includes [<id>] in the filename
            if f.find(f"[{vid}]") != -1:
                return os.path.join(root, f)
    return None


def _custom_archive_has(path: str, key: str) -> bool:
    if not key or not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return any(ln.strip() == f"custom {key}" for ln in f)
    except Exception:
        return False


def _custom_archive_add(path: str, key: str) -> None:
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"custom {key}\n")
    except Exception:
        pass


def _download_one(
    url: str, s: Settings, drive: DriveClient | None, ulog: UploadLog | None
) -> tuple[str, bool, str]:
    try:
        # skip se já registrado no nosso arquivo
        if s.archive_id and _custom_archive_has(s.archive_file, s.archive_id):
            return (url, True, "skipped (custom archive)")

        with YoutubeDL(_base_opts(s)) as ydl:
            ydl.download([url])

        with YoutubeDL(_base_opts(s)) as ydl:
            ydl.download([url])
        # post-upload (optional)
        if s.archive_id:
            _custom_archive_add(s.archive_file, s.archive_id)
            vid = _video_id_from_url(url)
            if not vid:
                return (url, True, "downloaded; no video id parsed for upload")
            if ulog and ulog.has(vid):
                return (url, True, "downloaded; already uploaded (log)")
            local = _find_media_by_id(s.out_dir, vid)
            if not local:
                return (url, True, "downloaded; media file not found for upload")
            # Mirror the relative folder structure under drive_root
            rel_dir = os.path.relpath(os.path.dirname(local), s.out_dir)
            parts = [p for p in rel_dir.split(os.sep) if p and p != "."]
            # prepend root
            if drive is None:
                return (url, True, "downloaded; drive client not initialized")
            folder_id = drive.ensure_path([s.drive_root] + parts)
            file_id = drive.upload_file(local, folder_id)
            if ulog:
                ulog.add(vid, local, file_id)
        return (url, True, "ok")
    except Exception as e:
        return (url, False, str(e))


@app.command()
def list(
    source: str = typer.Argument(
        ..., help="URL (channel/playlist/video) or path to a .txt with URLs"
    ),
    limit: t.Optional[int] = typer.Option(None, help="Limit number of items to show"),
):
    urls_in = _resolve_input(source)
    all_urls: list[str] = []
    for u in urls_in:
        all_urls.extend(_extract_entries(u, limit))
    for u in all_urls:
        print(u)


@app.command()
def download(
    source: str = typer.Argument(
        ..., help="URL (channel/playlist/video) or path to a .txt with URLs"
    ),
    out_dir: str = typer.Option("./downloads", help="Output directory"),
    archive_file: str = typer.Option(
        "./archive.txt", help="Skip already-downloaded IDs"
    ),
    fmt: str = typer.Option(
        "bv*+ba/b", help="yt-dlp format selector (default best video+audio)"
    ),
    max_res: t.Optional[int] = typer.Option(None, help="Cap max height, e.g. 1080"),
    subs: bool = typer.Option(True, help="Download subtitles"),
    auto_subs: bool = typer.Option(True, help="Also download auto-generated subs"),
    sub_langs: str = typer.Option("pt,en", help="Comma sep subtitle languages"),
    thumbnails: bool = typer.Option(True, help="Download thumbnails"),
    audio_only: bool = typer.Option(False, help="Extract audio to MP3"),
    workers: int = typer.Option(1, help="Parallel workers for multiple URLs"),
    limit: t.Optional[int] = typer.Option(
        None, help="Limit number of items from playlists/channels"
    ),
    dry_run: bool = typer.Option(False, help="Do not download; plan only"),
    # Drive
    drive_upload: bool = typer.Option(
        False, help="After each download, upload the media to Google Drive"
    ),
    drive_root: str = typer.Option("YouTubeArchive", help="Root folder name on Drive"),
    drive_credentials: str = typer.Option(
        "./credentials.json", help="Path to OAuth client credentials"
    ),
    drive_token: str = typer.Option("./token.json", help="Path to OAuth token cache"),
    uploaded_log: str = typer.Option(
        "./uploaded.jsonl", help="Path to JSONL log to avoid re-uploads"
    ),
    # Headers/cookies (opcionais)
    cookies_file: t.Optional[str] = typer.Option(
        None, help="Path to cookies.txt (Netscape)"
    ),
    referer: t.Optional[str] = typer.Option(None, help="Referer header"),
    origin: t.Optional[str] = typer.Option(None, help="Origin header"),
    user_agent: str = typer.Option("yt-archiver", help="User-Agent header"),
    concurrent_fragments: int = typer.Option(
        10, help="Number of concurrent fragments (yt-dlp -N)"
    ),
    # Naming (opcional)
    path: t.Optional[str] = typer.Option(
        None, help="Subpasta sob --out-dir, ex.: 'rocketSeat/Go/Introdução'"
    ),
    file_name: t.Optional[str] = typer.Option(
        None, help="Nome base do arquivo, ex.: 'Aula 01' (extensão automática)"
    ),
    archive_id: t.Optional[str] = typer.Option(
        None,
        help="ID manual para registrar/pular no archive.txt (desativa o archive nativo do yt-dlp neste run)",
    ),
):
    target_dir = os.path.join(out_dir, path) if path else out_dir
    os.makedirs(target_dir, exist_ok=True)
    s = Settings(
        out_dir=out_dir,
        archive_file=archive_file,
        fmt=fmt,
        max_res=max_res,
        subs=subs,
        auto_subs=auto_subs,
        sub_langs=sub_langs,
        thumbnails=thumbnails,
        audio_only=audio_only,
        workers=workers,
        limit=limit,
        dry_run=dry_run,
        drive_upload=drive_upload,
        drive_root=drive_root,
        drive_credentials=drive_credentials,
        drive_token=drive_token,
        uploaded_log=uploaded_log,
        cookies_file=cookies_file,
        referer=referer,
        origin=origin,
        user_agent=user_agent,
        concurrent_fragments=concurrent_fragments,
        custom_path=path,
        file_name=file_name,
        archive_id=archive_id,
    )

    sources = _resolve_input(source)

    # Build explicit list if parallelism/limit/dry-run
    urls: list[str] = []
    for u in sources:
        if workers > 1 or limit is not None or dry_run:
            urls.extend(_extract_entries(u, limit))
        else:
            urls.append(u)

    if not urls:
        console.print("[yellow]No URLs resolved from source(s). Nothing to do.")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Items to process: {len(urls)} | out={out_dir}[/cyan]")

    drive_client = None
    ulog = None
    if drive_upload:
        drive_client = DriveClient(s.drive_credentials, s.drive_token)
        ulog = UploadLog(s.uploaded_log)

    if workers <= 1:
        for u in track(urls, description="Downloading"):
            url, ok, msg = _download_one(u, s, drive_client, ulog)
            if not ok:
                console.print(f"[red]Failed:[/] {url} — {msg}")
            elif msg != "ok":
                console.print(f"[yellow]{msg}[/] — {url}")
        return

    # Parallel pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_download_one, u, s, drive_client, ulog) for u in urls]
        for f in track(
            concurrent.futures.as_completed(futs),
            total=len(futs),
            description="Downloading in parallel",
        ):
            url, ok, msg = f.result()
            if not ok:
                console.print(f"[red]Failed:[/] {url} — {msg}")
            elif msg != "ok":
                console.print(f"[yellow]{msg}[/] — {url}")


if __name__ == "__main__":
    app()

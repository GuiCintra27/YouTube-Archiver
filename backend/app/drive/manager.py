"""
Google Drive Manager - handles OAuth, uploads, downloads, and sync.
"""
from __future__ import annotations
import os
import random
import socket
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Callable

import httplib2
import google_auth_httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import requests

from app.config import settings
from app.core.logging import get_module_logger
from app.core.http import request_with_retry
from app.core.thumbnail import ensure_thumbnail

logger = get_module_logger("drive")

SCOPES = ['https://www.googleapis.com/auth/drive']
DRIVE_ROOT_FOLDER = "YouTube Archiver"


class DriveManager:
    """Google Drive manager with OAuth and sync support"""

    def __init__(
        self,
        credentials_path: str = "./credentials.json",
        token_path: str = "./token.json",
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._service = None
        self._service_local = threading.local()
        self._lock = threading.Lock()
        self._root_folder_id = None
        self._folder_cache: Dict[tuple[str, str], str] = {}
        self._folder_lock = threading.Lock()

    def get_auth_url(self) -> str:
        """Generate OAuth authentication URL"""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")

        flow = Flow.from_client_secrets_file(
            self.credentials_path,
            scopes=SCOPES,
            redirect_uri='http://localhost:8000/api/drive/oauth2callback'
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )

        return auth_url

    def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for tokens"""
        flow = Flow.from_client_secrets_file(
            self.credentials_path,
            scopes=SCOPES,
            redirect_uri='http://localhost:8000/api/drive/oauth2callback'
        )

        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save token
        with open(self.token_path, 'w') as token:
            token.write(creds.to_json())

        return {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        }

    def is_authenticated(self) -> bool:
        """Check if valid token exists, refreshing if necessary"""
        if not os.path.exists(self.token_path):
            return False

        try:
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

            if not creds:
                return False

            # If token is valid, authenticated
            if creds.valid:
                return True

            # If expired but has refresh token, try to refresh
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save updated token
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                    return True
                except Exception as e:
                    logger.debug(f"Failed to refresh token: {e}")
                    return False

            return False
        except Exception as e:
            logger.debug(f"Error checking authentication: {e}")
            return False

    def credentials_exist(self) -> bool:
        """Check if credentials file exists"""
        return os.path.exists(self.credentials_path)

    def get_service(self):
        """Get authenticated Google Drive service"""
        cached = getattr(self._service_local, "service", None)
        if cached is not None:
            return cached

        with self._lock:
            creds = None
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    # Update saved token
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                else:
                    raise Exception("Not authenticated. Please authenticate first.")

            http = httplib2.Http(timeout=settings.DRIVE_API_TIMEOUT)
            try:
                # Prevent 308 "Resume Incomplete" from being treated as redirect.
                redirect_codes = set(getattr(http, "redirect_codes", []))
                if 308 in redirect_codes:
                    redirect_codes.discard(308)
                    http.redirect_codes = redirect_codes
            except Exception:
                pass
            authed_http = google_auth_httplib2.AuthorizedHttp(creds, http=http)
            service = build('drive', 'v3', http=authed_http, cache_discovery=False)
            self._service_local.service = service
            if threading.current_thread().name == "MainThread":
                self._service = service
            return service

    def _get_access_token(self) -> str:
        """Get a valid OAuth access token (refreshing if needed)."""
        with self._lock:
            if not os.path.exists(self.token_path):
                raise Exception("Not authenticated. Please authenticate first.")

            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                else:
                    raise Exception("Not authenticated. Please authenticate first.")

            if not creds.token:
                raise Exception("Authentication token missing.")

            return str(creds.token)

    def get_access_token(self) -> str:
        """Public wrapper to return a valid OAuth access token."""
        return self._get_access_token()

    def _reset_service_cache(self) -> None:
        try:
            if hasattr(self._service_local, "service"):
                delattr(self._service_local, "service")
        except Exception:
            self._service_local.service = None
        if threading.current_thread().name == "MainThread":
            self._service = None

    def _should_retry_exception(self, exc: Exception) -> bool:
        if isinstance(exc, HttpError):
            status = getattr(exc, "resp", None)
            status_code = status.status if status else None
            return bool(status_code in set(settings.DRIVE_UPLOAD_RETRY_STATUSES))
        if isinstance(
            exc,
            (
                socket.gaierror,
                TimeoutError,
                ConnectionError,
                OSError,
                httplib2.error.RedirectMissingLocation,
                httplib2.error.RedirectLimit,
                httplib2.ServerNotFoundError,
                httplib2.HttpLib2Error,
                requests.RequestException,
            ),
        ):
            return True
        return False

    def _retry_sleep(self, attempt: int, backoff: float) -> None:
        sleep_for = backoff * (2 ** max(attempt - 1, 0))
        jitter = random.uniform(0.9, 1.1)
        time.sleep(sleep_for * jitter)

    def _execute_request_with_retry(
        self,
        request_factory: Callable[[], object],
        *,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
        label: Optional[str] = None,
    ) -> Dict:
        max_retries = settings.DRIVE_UPLOAD_RETRIES if retries is None else retries
        backoff = settings.DRIVE_UPLOAD_BACKOFF if backoff is None else backoff
        attempt = 0
        while True:
            try:
                request = request_factory()
                return request.execute()
            except Exception as exc:
                if attempt >= max_retries or not self._should_retry_exception(exc):
                    raise
                attempt += 1
                self._reset_service_cache()
                logger.warning(
                    "Drive API retry %s/%s (%s): %s",
                    attempt,
                    max_retries,
                    label or "request",
                    exc,
                )
                self._retry_sleep(attempt, backoff)

    def _run_resumable_upload(
        self,
        request_factory: Callable[[], object],
        *,
        on_status: Optional[Callable[[object], None]] = None,
        label: Optional[str] = None,
    ) -> Dict:
        max_retries = settings.DRIVE_UPLOAD_RETRIES
        backoff = settings.DRIVE_UPLOAD_BACKOFF
        attempt = 0
        request = request_factory()
        response = None
        while response is None:
            try:
                status, response = request.next_chunk()
                if status and on_status:
                    on_status(status)
            except Exception as exc:
                if attempt >= max_retries or not self._should_retry_exception(exc):
                    raise
                attempt += 1
                self._reset_service_cache()
                if isinstance(exc, httplib2.error.RedirectMissingLocation):
                    request = request_factory()
                logger.warning(
                    "Drive upload retry %s/%s (%s): %s",
                    attempt,
                    max_retries,
                    label or "resumable_upload",
                    exc,
                )
                self._retry_sleep(attempt, backoff)
        return response

    def _list_files_with_pagination(
        self,
        *,
        query: str,
        fields: str,
        page_size: Optional[int] = None,
        label: Optional[str] = None,
    ) -> List[Dict]:
        service = self.get_service()
        page_size = page_size or settings.DRIVE_LIST_PAGE_SIZE
        page_token = None
        items: List[Dict] = []
        while True:
            def _request():
                return service.files().list(
                    q=query,
                    fields=f"nextPageToken, {fields}",
                    pageSize=page_size,
                    pageToken=page_token,
                )

            results = self._execute_request_with_retry(
                _request,
                label=label or "drive.list",
            )
            items.extend(results.get("files", []))
            page_token = results.get("nextPageToken")
            if not page_token:
                break
        return items
    def _drive_api_get_json(self, url: str, params: Dict[str, str]) -> Dict:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        resp = request_with_retry(
            "GET",
            url,
            headers=headers,
            params=params,
            timeout=(settings.DRIVE_HTTP_TIMEOUT_CONNECT, settings.DRIVE_HTTP_TIMEOUT_READ),
            retries=settings.DRIVE_HTTP_RETRIES,
            backoff=settings.DRIVE_HTTP_BACKOFF,
        )
        if resp.status_code >= 400:
            raise Exception(f"Drive API error {resp.status_code}: {resp.text}")

        data = resp.json()
        if not isinstance(data, dict):
            raise Exception("Invalid Drive API response (expected JSON object).")
        return data

    def _drive_api_download_to_path(
        self,
        file_id: str,
        dest_path: Path,
        expected_size: int = 0,
        progress_callback: Optional[Callable] = None,
        file_name: Optional[str] = None,
    ) -> int:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}"
        params = {"alt": "media", "acknowledgeAbuse": "true"}

        tmp_path = dest_path.with_suffix(dest_path.suffix + ".part")
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass

        downloaded_bytes = 0
        try:
            with request_with_retry(
                "GET",
                url,
                headers=headers,
                params=params,
                stream=True,
                timeout=(settings.DRIVE_HTTP_TIMEOUT_CONNECT, settings.DRIVE_STREAM_TIMEOUT_READ),
                retries=0,
            ) as resp:
                if resp.status_code >= 400:
                    raise Exception(f"Drive download error {resp.status_code}: {resp.text}")

                tmp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(tmp_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded_bytes += len(chunk)

                        if progress_callback and expected_size > 0:
                            percent = int((downloaded_bytes / expected_size) * 100)
                            if percent > 99:
                                percent = 99
                            progress_callback({
                                "file_name": file_name or dest_path.name,
                                "progress": percent,
                            })

            if expected_size > 0 and downloaded_bytes != expected_size:
                raise Exception(
                    f"Incomplete download (expected {expected_size} bytes, got {downloaded_bytes})"
                )

            tmp_path.replace(dest_path)
            return downloaded_bytes
        except Exception:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                pass
            raise

    def get_or_create_root_folder(self) -> str:
        """Get or create the root 'YouTube Archiver' folder"""
        with self._folder_lock:
            if self._root_folder_id:
                return self._root_folder_id

            service = self.get_service()

            # Search for existing folder
            query = f"name='{DRIVE_ROOT_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self._execute_request_with_retry(
                lambda: service.files().list(q=query, fields='files(id, name)'),
                label="drive.root.list",
            )
            files = results.get('files', [])

            if files:
                self._root_folder_id = files[0]['id']
                return self._root_folder_id

            # Create folder
            folder_metadata = {
                'name': DRIVE_ROOT_FOLDER,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self._execute_request_with_retry(
                lambda: service.files().create(body=folder_metadata, fields='id'),
                label="drive.root.create",
            )
            self._root_folder_id = folder['id']
            return self._root_folder_id

    def ensure_folder(self, name: str, parent_id: str) -> str:
        """Ensure a folder exists, creating if necessary"""
        cache_key = (parent_id, name)
        cached_id = self._folder_cache.get(cache_key)
        if cached_id:
            return cached_id

        with self._folder_lock:
            cached_id = self._folder_cache.get(cache_key)
            if cached_id:
                return cached_id

            service = self.get_service()

            # Escape single quotes in folder name for query
            escaped_name = name.replace("'", "\\'")
            query = f"name='{escaped_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
            results = self._execute_request_with_retry(
                lambda: service.files().list(q=query, fields='files(id)'),
                label="drive.folder.list",
            )
            files = results.get('files', [])

            if files:
                folder_id = files[0]['id']
                self._folder_cache[cache_key] = folder_id
                return folder_id

            # Create folder
            folder_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = self._execute_request_with_retry(
                lambda: service.files().create(body=folder_metadata, fields='id'),
                label="drive.folder.create",
            )
            folder_id = folder['id']
            self._folder_cache[cache_key] = folder_id
            return folder_id

    def upload_video(
        self,
        local_path: str,
        relative_path: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Upload a video to Drive maintaining folder structure.
        Also uploads related files (thumbnails, metadata, subtitles).
        """
        try:
            service = self.get_service()
            root_id = self.get_or_create_root_folder()

            # Create folder structure
            path_parts = Path(relative_path).parts
            current_parent = root_id

            # Create all intermediate folders
            for folder_name in path_parts[:-1]:
                current_parent = self.ensure_folder(folder_name, current_parent)

            # Video filename
            file_name = path_parts[-1]
            video_path = Path(local_path)
            base_name = video_path.stem

            logger.debug(f"Uploading video: {file_name}")
            logger.debug(f"Local path: {local_path}")

            # Check if video file already exists
            escaped_file_name = file_name.replace("'", "\\'")
            query = f"name='{escaped_file_name}' and '{current_parent}' in parents and trashed=false"
            logger.debug(f"Query: {query}")

            results = self._execute_request_with_retry(
                lambda: service.files().list(q=query, fields='files(id, name, size)'),
                label="drive.upload.check_exists",
            )
            existing_files = results.get('files', [])

            if existing_files:
                logger.debug(f"File already exists in Drive: {file_name}")
                existing = existing_files[0]
                return {
                    "status": "skipped",
                    "message": "File already exists in Drive",
                    "file_id": existing.get('id'),
                    "file_name": file_name,
                    "size": int(existing.get('size') or 0),
                }

            # Ensure thumbnail exists (generate if missing)
            thumbnail_path, thumbnail_generated = ensure_thumbnail(video_path)
            if thumbnail_generated:
                logger.info(f"Auto-generated thumbnail for: {file_name}")

            # Find related files (thumbnail, metadata, subtitles)
            parent_dir = video_path.parent
            related_files = []

            # Related file extensions to upload
            related_extensions = [
                '.jpg', '.jpeg', '.png', '.webp',  # Thumbnails
                '.info.json',  # Metadata
                '.vtt', '.srt', '.ass',  # Subtitles
                '.description',  # Description
                '.ytarchiver.json',  # Catalog ID sidecar
            ]

            for file in parent_dir.iterdir():
                if file.is_file() and file != video_path:
                    if file.name.startswith(base_name + "."):
                        if any(file.name.endswith(ext) for ext in related_extensions):
                            related_files.append(file)

            # Upload main video
            file_metadata = {
                'name': file_name,
                'parents': [current_parent]
            }

            logger.debug(f"Starting upload for {file_name}...")

            def request_factory():
                current_service = self.get_service()
                media = MediaFileUpload(
                    local_path,
                    resumable=True,
                    chunksize=settings.DRIVE_UPLOAD_CHUNK_SIZE,
                )
                return current_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, size'
                )

            def on_status(status):
                if status and progress_callback:
                    progress_callback({
                        "file_name": file_name,
                        "progress": int(status.progress() * 100)
                    })

            response = self._run_resumable_upload(
                request_factory,
                on_status=on_status,
                label="drive.upload.next_chunk",
            )

            logger.info(f"Upload completed: {file_name} (ID: {response['id']})")

            uploaded_related = []
            related_files_detailed: List[Dict] = []
            related_files_failed: List[Dict] = []
            # Upload related files
            for related_file in related_files:
                try:
                    # Check if already exists
                    escaped_related_name = related_file.name.replace("'", "\\'")
                    query = f"name='{escaped_related_name}' and '{current_parent}' in parents and trashed=false"
                    results = self._execute_request_with_retry(
                        lambda: service.files().list(q=query, fields='files(id)'),
                        label="drive.upload.related.check",
                    )
                    if results.get('files', []):
                        existing_id = results["files"][0].get("id")
                        related_files_detailed.append(
                            {
                                "name": related_file.name,
                                "file_id": existing_id,
                                "status": "skipped",
                            }
                        )
                        continue  # Already exists, skip

                    # Upload
                    related_metadata = {
                        'name': related_file.name,
                        'parents': [current_parent]
                    }
                    related_media = MediaFileUpload(str(related_file))
                    related_resp = self._execute_request_with_retry(
                        lambda: service.files().create(
                            body=related_metadata,
                            media_body=related_media,
                            fields='id, name'
                        ),
                        label="drive.upload.related.create",
                    )
                    uploaded_related.append(related_file.name)
                    related_files_detailed.append(
                        {
                            "name": related_resp.get("name") or related_file.name,
                            "file_id": related_resp.get("id"),
                            "status": "success",
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to upload related file {related_file.name}: {e}")
                    related_files_failed.append(
                        {
                            "name": related_file.name,
                            "error": str(e),
                        }
                    )

            return {
                "status": "success",
                "file_id": response['id'],
                "file_name": response['name'],
                "size": response.get('size', 0),
                "related_files": uploaded_related,
                "related_files_detailed": related_files_detailed,
                "related_files_failed": related_files_failed,
                "thumbnail_generated": thumbnail_generated,
            }

        except Exception as e:
            logger.error(f"Exception in upload_video: {e}", exc_info=True)
            raise

    def list_videos(self) -> List[Dict]:
        """List all videos in the Drive folder"""
        root_id = self.get_or_create_root_folder()

        videos = []
        # Store thumbnails by folder_id and base_name for matching
        thumbnails_by_folder: Dict[str, Dict[str, Dict]] = {}

        def scan_folder(folder_id: str, path_prefix: str = ""):
            """Recursively scan a folder"""
            query = f"'{folder_id}' in parents and trashed=false"
            items = self._list_files_with_pagination(
                query=query,
                fields='files(id, name, mimeType, size, createdTime, modifiedTime, thumbnailLink)',
                label="drive.list_folder",
            )

            # First pass: collect thumbnails
            for item in items:
                if item['mimeType'] != 'application/vnd.google-apps.folder':
                    ext = Path(item['name']).suffix.lower()
                    if ext in settings.THUMBNAIL_EXTENSIONS:
                        # Store thumbnail by folder and base name
                        base_name = Path(item['name']).stem
                        if folder_id not in thumbnails_by_folder:
                            thumbnails_by_folder[folder_id] = {}
                        thumbnails_by_folder[folder_id][base_name] = {
                            'id': item['id'],
                            'name': item['name'],
                            'mimeType': item.get('mimeType', 'image/jpeg')
                        }

            # Second pass: collect videos and folders
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recurse into subfolders
                    new_path = f"{path_prefix}/{item['name']}" if path_prefix else item['name']
                    scan_folder(item['id'], new_path)
                else:
                    # It's a file
                    ext = Path(item['name']).suffix.lower()
                    if ext in settings.VIDEO_EXTENSIONS:
                        video_base_name = Path(item['name']).stem
                        drive_thumbnail = item.get('thumbnailLink')
                        custom_thumbnail_id = None

                        # Look for a custom thumbnail file with the same base name
                        if folder_id in thumbnails_by_folder:
                            custom_thumb = thumbnails_by_folder[folder_id].get(video_base_name)
                            if custom_thumb:
                                custom_thumbnail_id = custom_thumb['id']

                        videos.append({
                            "id": item['id'],
                            "name": item['name'],
                            "path": f"{path_prefix}/{item['name']}" if path_prefix else item['name'],
                            "size": int(item.get('size', 0)),
                            "created_at": item.get('createdTime'),
                            "modified_at": item.get('modifiedTime'),
                            "thumbnail": drive_thumbnail,
                            "custom_thumbnail_id": custom_thumbnail_id,
                        })

        scan_folder(root_id)
        return videos

    def get_sync_state(self, local_base_dir: str = "./downloads") -> Dict:
        """
        Compare local vs Drive state and return differences.
        """
        # List local videos
        local_videos = set()
        base_path = Path(local_base_dir)

        if base_path.exists():
            for video_file in base_path.rglob('*'):
                if video_file.suffix.lower() in settings.VIDEO_EXTENSIONS:
                    rel_path = video_file.relative_to(base_path)
                    local_videos.add(str(rel_path))

        # List Drive videos
        drive_videos_list = self.list_videos()
        drive_videos = {v['path'] for v in drive_videos_list}

        return {
            "local_only": sorted(list(local_videos - drive_videos)),
            "drive_only": sorted(list(drive_videos - local_videos)),
            "synced": sorted(list(local_videos & drive_videos)),
            "total_local": len(local_videos),
            "total_drive": len(drive_videos),
        }

    def upload_to_folder(
        self,
        folder_name: str,
        files: List[str],
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Upload multiple files to a specific folder in Drive.
        Creates folder inside "YouTube Archiver" if it doesn't exist.

        Args:
            folder_name: Name of the folder to create/use inside root
            files: List of local file paths to upload
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with status, uploaded files, and any errors
        """
        try:
            service = self.get_service()
            root_id = self.get_or_create_root_folder()

            # Create/get the target folder
            target_folder_id = self.ensure_folder(folder_name, root_id)

            # Generate thumbnails for videos that don't have one
            files_to_upload = list(files)  # Make a copy
            generated_thumbnails = []

            for file_path in files:
                file_path = Path(file_path)
                if file_path.suffix.lower() in settings.VIDEO_EXTENSIONS:
                    # Check if there's already a thumbnail in the list
                    base_name = file_path.stem
                    has_thumbnail = any(
                        Path(f).stem == base_name and Path(f).suffix.lower() in settings.THUMBNAIL_EXTENSIONS
                        for f in files
                    )

                    if not has_thumbnail:
                        # Generate thumbnail
                        thumbnail_path, generated = ensure_thumbnail(file_path)
                        if thumbnail_path and generated:
                            files_to_upload.append(str(thumbnail_path))
                            generated_thumbnails.append(str(thumbnail_path))
                            logger.info(f"Auto-generated thumbnail for external upload: {file_path.name}")

            uploaded_files = []
            failed_files = []
            total_files = len(files_to_upload)

            for index, file_path in enumerate(files_to_upload):
                try:
                    file_path = Path(file_path)
                    if not file_path.exists():
                        failed_files.append({
                            "file": str(file_path),
                            "error": "File not found"
                        })
                        continue

                    file_name = file_path.name

                    # Check if file already exists
                    escaped_name = file_name.replace("'", "\\'")
                    query = f"name='{escaped_name}' and '{target_folder_id}' in parents and trashed=false"
                    results = self._execute_request_with_retry(
                        lambda: service.files().list(q=query, fields='files(id, size)'),
                        label="drive.external.check_exists",
                    )

                    if results.get('files', []):
                        logger.debug(f"File already exists, skipping: {file_name}")
                        existing_id = results["files"][0].get("id")
                        uploaded_files.append({
                            "name": file_name,
                            "file_id": existing_id,
                            "size": int(results["files"][0].get("size") or 0),
                            "status": "skipped",
                            "message": "Already exists"
                        })
                        continue

                    # Upload file
                    file_metadata = {
                        'name': file_name,
                        'parents': [target_folder_id]
                    }

                    # Use resumable upload for larger files
                    file_size = file_path.stat().st_size
                    if file_size > 5 * 1024 * 1024:  # > 5MB
                        def request_factory():
                            current_service = self.get_service()
                            media = MediaFileUpload(
                                str(file_path),
                                resumable=True,
                                chunksize=settings.DRIVE_UPLOAD_CHUNK_SIZE
                            )
                            return current_service.files().create(
                                body=file_metadata,
                                media_body=media,
                                fields='id, name, size'
                            )

                        def on_status(status):
                            if status and progress_callback:
                                file_progress = int(status.progress() * 100)
                                overall_progress = int(((index + status.progress()) / total_files) * 100)
                                progress_callback({
                                    "current_file": file_name,
                                    "file_progress": file_progress,
                                    "overall_progress": overall_progress,
                                    "files_uploaded": index,
                                    "total_files": total_files
                                })

                        response = self._run_resumable_upload(
                            request_factory,
                            on_status=on_status,
                            label="drive.external.next_chunk",
                        )
                    else:
                        media = MediaFileUpload(str(file_path))
                        response = self._execute_request_with_retry(
                            lambda: service.files().create(
                                body=file_metadata,
                                media_body=media,
                                fields='id, name, size'
                            ),
                            label="drive.external.create",
                        )

                    uploaded_files.append({
                        "name": file_name,
                        "file_id": response['id'],
                        "size": int(response.get('size', 0)),
                        "status": "success"
                    })

                    logger.info(f"Uploaded: {file_name} (ID: {response['id']})")

                    # Update progress after file completion
                    if progress_callback:
                        progress_callback({
                            "current_file": file_name,
                            "file_progress": 100,
                            "overall_progress": int(((index + 1) / total_files) * 100),
                            "files_uploaded": index + 1,
                            "total_files": total_files
                        })

                except Exception as e:
                    logger.error(f"Failed to upload {file_path}: {e}")
                    failed_files.append({
                        "file": str(file_path),
                        "error": str(e)
                    })

            return {
                "status": "success" if not failed_files else "partial",
                "folder_name": folder_name,
                "folder_id": target_folder_id,
                "uploaded": uploaded_files,
                "failed": failed_files,
                "total_uploaded": len([f for f in uploaded_files if f.get("status") == "success"]),
                "total_skipped": len([f for f in uploaded_files if f.get("status") == "skipped"]),
                "total_failed": len(failed_files),
                "generated_thumbnails": generated_thumbnails,
            }

        except Exception as e:
            logger.error(f"Error in upload_to_folder: {e}", exc_info=True)
            raise

    def download_file(
        self,
        file_id: str,
        relative_path: str,
        local_base_dir: str = "./downloads",
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Download a file from Drive to local storage.

        Args:
            file_id: Google Drive file ID
            relative_path: Relative path in Drive (e.g., "Channel/video.mp4")
            local_base_dir: Local base directory for downloads
            progress_callback: Optional callback for progress updates

        Returns:
            Dict with status and file info
        """
        try:
            file_metadata = self._drive_api_get_json(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                {"fields": "name,size,mimeType,parents"},
            )

            file_name = file_metadata.get("name", "unknown")
            file_size = int(file_metadata.get("size") or 0)

            # Create local directory structure
            local_path = Path(local_base_dir) / relative_path
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if file already exists locally
            if local_path.exists():
                local_size = local_path.stat().st_size
                if local_size == file_size:
                    logger.debug(f"File already exists locally: {relative_path}")
                    return {
                        "status": "skipped",
                        "message": "File already exists locally",
                        "file_name": file_name,
                        "path": str(local_path)
                    }

            logger.debug(f"Downloading: {file_name} to {local_path}")

            self._drive_api_download_to_path(
                file_id=file_id,
                dest_path=local_path,
                expected_size=file_size,
                progress_callback=progress_callback,
                file_name=file_name,
            )

            logger.info(f"Download completed: {file_name}")

            # Also download related files (thumbnails, metadata, subtitles)
            downloaded_related = self._download_related_files(
                file_id=file_id,
                video_name=file_name,
                local_dir=local_path.parent,
                parent_ids=file_metadata.get("parents") or [],
            )

            return {
                "status": "success",
                "file_name": file_name,
                "path": str(local_path),
                "size": file_size,
                "related_files": downloaded_related
            }

        except Exception as e:
            logger.error(f"Exception in download_file: {e}", exc_info=True)
            raise

    def _download_related_files(
        self,
        file_id: str,
        video_name: str,
        local_dir: Path,
        parent_ids: List[str],
    ) -> List[str]:
        """
        Download related files (thumbnails, metadata, subtitles) for a video.

        Args:
            file_id: The video file ID to find parent folder
            video_name: Video filename to match related files
            local_dir: Local directory to save files
            parent_ids: Drive parent ids of the video file

        Returns:
            List of downloaded related file names
        """
        try:
            base_name = Path(video_name).stem

            if not parent_ids:
                return []

            parent_id = parent_ids[0]

            # Related file extensions
            related_extensions = [
                '.jpg', '.jpeg', '.png', '.webp',  # Thumbnails
                '.info.json',  # Metadata
                '.vtt', '.srt', '.ass',  # Subtitles
                '.description',  # Description
                '.ytarchiver.json',  # Catalog ID sidecar
            ]

            # Search for related files in same folder
            escaped_base_name = base_name.replace("'", "\\'")
            query = f"'{parent_id}' in parents and name contains '{escaped_base_name}' and trashed=false"
            results = self._drive_api_get_json(
                "https://www.googleapis.com/drive/v3/files",
                {"q": query, "fields": "files(id,name,size,mimeType)", "pageSize": "1000"},
            )

            downloaded = []
            for item in results.get("files", []):
                item_name = item.get("name") or ""
                # Skip the video itself
                if item_name == video_name:
                    continue

                # Check if it's a related file
                if any(item_name.endswith(ext) for ext in related_extensions):
                    local_file_path = local_dir / item_name

                    # Skip if already exists
                    if local_file_path.exists():
                        continue

                    try:
                        item_id = item.get("id")
                        if not item_id:
                            continue
                        item_size = int(item.get("size") or 0)
                        self._drive_api_download_to_path(
                            file_id=str(item_id),
                            dest_path=local_file_path,
                            expected_size=item_size,
                            progress_callback=None,
                            file_name=item_name,
                        )

                        downloaded.append(item_name)
                        logger.debug(f"Downloaded related file: {item_name}")

                    except Exception as e:
                        logger.warning(f"Failed to download related file {item_name}: {e}")

            return downloaded

        except Exception as e:
            logger.warning(f"Error downloading related files: {e}")
            return []

    def get_video_by_path(self, relative_path: str) -> Optional[Dict]:
        """
        Find a video in Drive by its relative path.

        Args:
            relative_path: Path like "Channel/video.mp4"

        Returns:
            Video metadata dict or None if not found
        """
        videos = self.list_videos()
        for video in videos:
            if video['path'] == relative_path:
                return video
        return None

    def delete_video(self, file_id: str) -> bool:
        """Remove a video from Drive"""
        service = self.get_service()
        try:
            service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False

    def _list_related_files(self, parent_id: str, base_name: str) -> List[Dict]:
        """List related files (thumbs, metadata, subtitles) in a Drive folder."""
        service = self.get_service()
        related_extensions = [ext.lower() for ext in settings.THUMBNAIL_EXTENSIONS] + [
            ".info.json",
            ".vtt",
            ".srt",
            ".ass",
            ".description",
            ".txt",
        ]

        escaped_base = base_name.replace("'", "\\'")
        query = f"'{parent_id}' in parents and name contains '{escaped_base}' and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id, name)",
        ).execute()

        related = []
        for item in results.get("files", []):
            name = item.get("name") or ""
            if not name.startswith(base_name + "."):
                continue
            remaining = name[len(base_name):]
            remaining_lower = remaining.lower()
            if any(remaining_lower.endswith(ext) or remaining_lower == ext for ext in related_extensions):
                related.append({"id": item.get("id"), "name": name})
        return related

    def delete_video_with_related(
        self,
        file_id: str,
        related_file_ids: Optional[List[str]] = None,
    ) -> Dict:
        """
        Remove a video from Drive along with related files (thumbnails, subtitles, metadata).

        Returns:
            Dict with deleted/failed lists and candidate parent folder ids.
        """
        service = self.get_service()
        related_ids = set(related_file_ids or [])
        parent_ids: List[str] = []
        base_name: Optional[str] = None

        try:
            metadata = service.files().get(
                fileId=file_id,
                fields="id, name, parents",
            ).execute()
            name = metadata.get("name")
            base_name = Path(name).stem if name else None
            parent_ids = metadata.get("parents", []) or []
        except HttpError as e:
            if getattr(e, "resp", None) is not None and e.resp.status == 404:
                logger.warning(f"Drive file not found (delete): {file_id}")
            else:
                logger.error(f"Error reading Drive metadata {file_id}: {e}")
                raise

        if base_name and parent_ids:
            try:
                fallback_related = self._list_related_files(parent_ids[0], base_name)
                related_ids.update([item["id"] for item in fallback_related if item.get("id")])
            except Exception as e:
                logger.warning(f"Failed to list related files for {file_id}: {e}")

        to_delete = {file_id}
        to_delete.update({rid for rid in related_ids if isinstance(rid, str) and rid})

        deleted: List[str] = []
        failed: List[Dict[str, str]] = []
        missing: List[str] = []

        for target_id in to_delete:
            try:
                service.files().delete(fileId=target_id).execute()
                deleted.append(target_id)
            except HttpError as e:
                if getattr(e, "resp", None) is not None and e.resp.status == 404:
                    missing.append(target_id)
                    deleted.append(target_id)
                else:
                    failed.append({"file_id": target_id, "error": str(e)})
            except Exception as e:
                failed.append({"file_id": target_id, "error": str(e)})

        return {
            "deleted": deleted,
            "failed": failed,
            "missing": missing,
            "total_deleted": len(deleted),
            "total_failed": len(failed),
            "parent_ids": parent_ids,
            "video_deleted": file_id in deleted,
        }

    def delete_videos_with_related(
        self,
        file_ids: List[str],
        related_map: Optional[Dict[str, List[str]]] = None,
    ) -> Dict:
        """
        Delete multiple videos and their related files.
        """
        deleted: List[str] = []
        failed: List[Dict[str, str]] = []
        missing: List[str] = []
        parent_ids: List[str] = []
        deleted_videos: List[str] = []

        for file_id in file_ids:
            try:
                related_ids = (related_map or {}).get(file_id) if related_map else None
                result = self.delete_video_with_related(file_id, related_ids)

                deleted.extend(result.get("deleted", []))
                failed.extend(result.get("failed", []))
                missing.extend(result.get("missing", []))
                parent_ids.extend(result.get("parent_ids", []))
                if result.get("video_deleted"):
                    deleted_videos.append(file_id)
            except Exception as e:
                failed.append({"file_id": file_id, "error": str(e)})

        return {
            "deleted": deleted,
            "failed": failed,
            "missing": missing,
            "parent_ids": list(dict.fromkeys(parent_ids)),
            "deleted_videos": deleted_videos,
            "total_deleted": len(deleted),
            "total_failed": len(failed),
        }

    def _folder_has_children(self, folder_id: str) -> bool:
        service = self.get_service()
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id)",
            pageSize=1,
        ).execute()
        return bool(results.get("files"))

    def cleanup_empty_folders(self, folder_ids: List[str], root_id: Optional[str] = None) -> Dict:
        """
        Recursively delete empty folders up to the root folder.

        Returns:
            Dict with deleted and skipped folders.
        """
        service = self.get_service()
        root_id = root_id or self.get_or_create_root_folder()
        deleted: List[Dict[str, str]] = []
        skipped: List[Dict[str, str]] = []
        visited = set()

        for folder_id in folder_ids:
            current_id = folder_id
            while current_id and current_id not in visited:
                visited.add(current_id)

                if current_id == root_id:
                    skipped.append({"folder_id": current_id, "reason": "root"})
                    break

                try:
                    if self._folder_has_children(current_id):
                        skipped.append({"folder_id": current_id, "reason": "not_empty"})
                        break

                    metadata = service.files().get(
                        fileId=current_id,
                        fields="id, name, parents, mimeType",
                    ).execute()
                    if metadata.get("mimeType") != "application/vnd.google-apps.folder":
                        skipped.append({"folder_id": current_id, "reason": "not_folder"})
                        break

                    folder_name = metadata.get("name") or ""
                    if folder_name == ".catalog":
                        skipped.append({"folder_id": current_id, "reason": "catalog"})
                        break

                    service.files().delete(fileId=current_id).execute()
                    deleted.append({"folder_id": current_id, "name": folder_name})

                    parents = metadata.get("parents", []) or []
                    current_id = parents[0] if parents else None
                except HttpError as e:
                    skipped.append({"folder_id": current_id, "reason": str(e)})
                    break
                except Exception as e:
                    skipped.append({"folder_id": current_id, "reason": str(e)})
                    break

        return {"deleted": deleted, "skipped": skipped}

    def rename_file(self, file_id: str, new_name: str) -> Dict:
        """
        Rename a file in Google Drive.

        Args:
            file_id: Google Drive file ID
            new_name: New name for the file (without extension)

        Returns:
            Dict with status and new file info
        """
        try:
            service = self.get_service()

            # Get current file metadata
            file_metadata = service.files().get(
                fileId=file_id,
                fields='name, parents'
            ).execute()

            old_name = file_metadata.get('name', '')
            old_extension = Path(old_name).suffix
            old_base_name = Path(old_name).stem

            # Create new filename with same extension
            new_full_name = new_name + old_extension

            # Update file name
            updated_metadata = {'name': new_full_name}
            updated_file = service.files().update(
                fileId=file_id,
                body=updated_metadata,
                fields='id, name'
            ).execute()

            logger.info(f"Renamed file: {old_name} -> {new_full_name}")

            # Try to rename related files (thumbnails, metadata, etc.)
            renamed_related = []
            parents = file_metadata.get('parents', [])
            if parents:
                parent_id = parents[0]
                renamed_related = self._rename_related_files(
                    parent_id, old_base_name, new_name
                )

            return {
                "status": "success",
                "message": "Arquivo renomeado com sucesso",
                "file_id": updated_file['id'],
                "new_name": updated_file['name'],
                "renamed_related": renamed_related,
            }

        except Exception as e:
            logger.error(f"Error renaming file {file_id}: {e}", exc_info=True)
            raise

    def _rename_related_files(
        self,
        parent_id: str,
        old_base_name: str,
        new_base_name: str
    ) -> List[str]:
        """
        Rename related files (thumbnails, metadata, subtitles) for a video.

        Args:
            parent_id: Parent folder ID
            old_base_name: Old base name (without extension)
            new_base_name: New base name (without extension)

        Returns:
            List of renamed file names
        """
        try:
            service = self.get_service()

            # Related file extensions
            related_extensions = [
                '.jpg', '.jpeg', '.png', '.webp',  # Thumbnails
                '.info.json',  # Metadata
                '.vtt', '.srt', '.ass',  # Subtitles
                '.description',  # Description
                '.ytarchiver.json',  # Catalog ID sidecar
            ]

            # Search for related files in same folder
            escaped_old_name = old_base_name.replace("'", "\\'")
            query = f"'{parent_id}' in parents and name contains '{escaped_old_name}' and trashed=false"
            results = service.files().list(
                q=query,
                fields='files(id, name)'
            ).execute()

            renamed = []
            for item in results.get('files', []):
                item_name = item['name']

                # Check if it's a related file (starts with old name and has related extension)
                if item_name.startswith(old_base_name + "."):
                    remaining = item_name[len(old_base_name):]  # Gets ".jpg", ".info.json", etc.

                    if any(remaining.endswith(ext) or remaining == ext for ext in related_extensions):
                        new_name = new_base_name + remaining

                        try:
                            service.files().update(
                                fileId=item['id'],
                                body={'name': new_name},
                                fields='id, name'
                            ).execute()
                            renamed.append(new_name)
                            logger.debug(f"Renamed related file: {item_name} -> {new_name}")
                        except Exception as e:
                            logger.warning(f"Failed to rename related file {item_name}: {e}")

            return renamed

        except Exception as e:
            logger.warning(f"Error renaming related files: {e}")
            return []

    def update_thumbnail(
        self,
        file_id: str,
        thumbnail_data: bytes,
        thumbnail_extension: str
    ) -> Dict:
        """
        Update/upload a new thumbnail for a video in Google Drive.

        Args:
            file_id: Video file ID in Drive
            thumbnail_data: Binary data of the new thumbnail
            thumbnail_extension: Extension of the thumbnail (e.g., '.jpg', '.png')

        Returns:
            Dict with status and thumbnail info
        """
        try:
            service = self.get_service()

            # Get video metadata to find folder and base name
            file_metadata = service.files().get(
                fileId=file_id,
                fields='name, parents'
            ).execute()

            video_name = file_metadata.get('name', '')
            video_base_name = Path(video_name).stem
            parents = file_metadata.get('parents', [])

            if not parents:
                raise Exception("Cannot find parent folder for video")

            parent_id = parents[0]

            # Delete old thumbnails
            for ext in settings.THUMBNAIL_EXTENSIONS:
                old_thumb_name = video_base_name + ext
                escaped_name = old_thumb_name.replace("'", "\\'")
                query = f"name='{escaped_name}' and '{parent_id}' in parents and trashed=false"
                results = service.files().list(q=query, fields='files(id)').execute()

                for old_file in results.get('files', []):
                    try:
                        service.files().delete(fileId=old_file['id']).execute()
                        logger.debug(f"Deleted old thumbnail: {old_thumb_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete old thumbnail: {e}")

            # Normalize extension
            if not thumbnail_extension.startswith('.'):
                thumbnail_extension = '.' + thumbnail_extension

            # Create new thumbnail file
            new_thumb_name = video_base_name + thumbnail_extension.lower()
            thumb_metadata = {
                'name': new_thumb_name,
                'parents': [parent_id]
            }

            # Create temporary file for upload
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=thumbnail_extension) as tmp:
                tmp.write(thumbnail_data)
                tmp_path = tmp.name

            try:
                media = MediaFileUpload(tmp_path)
                new_file = service.files().create(
                    body=thumb_metadata,
                    media_body=media,
                    fields='id, name'
                ).execute()

                logger.info(f"Uploaded new thumbnail: {new_thumb_name}")

                return {
                    "status": "success",
                    "message": "Thumbnail atualizada com sucesso",
                    "thumbnail_id": new_file['id'],
                    "thumbnail_name": new_file['name'],
                }
            finally:
                # Clean up temp file
                import os
                os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Error updating thumbnail for {file_id}: {e}", exc_info=True)
            raise

    def delete_videos_batch(self, file_ids: List[str]) -> Dict:
        """
        Delete multiple videos from Drive.

        Args:
            file_ids: List of file IDs to delete

        Returns:
            Dict with deleted count, failed list, and status
        """
        service = self.get_service()
        deleted = []
        failed = []

        for file_id in file_ids:
            try:
                service.files().delete(fileId=file_id).execute()
                deleted.append(file_id)
                logger.debug(f"Deleted file: {file_id}")
            except Exception as e:
                logger.error(f"Failed to delete file {file_id}: {e}")
                failed.append({"file_id": file_id, "error": str(e)})

        logger.info(f"Batch delete completed: {len(deleted)} deleted, {len(failed)} failed")

        return {
            "deleted": deleted,
            "failed": failed,
            "total_deleted": len(deleted),
            "total_failed": len(failed),
        }

    def get_file_metadata(self, file_id: str) -> Dict:
        """Get file metadata including size and mime type"""
        service = self.get_service()
        return service.files().get(
            fileId=file_id,
            fields='size, mimeType, name, parents'
        ).execute()

    def get_share_status(self, file_id: str) -> Dict:
        """Get current public sharing status for a file."""
        service = self.get_service()
        try:
            metadata = service.files().get(
                fileId=file_id,
                fields='id, webViewLink, permissions(id,type,role)'
            ).execute()
        except HttpError as e:
            logger.error(f"Failed to get share status for {file_id}: {e}")
            raise

        permissions = metadata.get("permissions", []) or []
        public_permission = None
        for permission in permissions:
            if permission.get("type") == "anyone" and permission.get("role") == "reader":
                public_permission = permission
                break

        shared = public_permission is not None
        return {
            "shared": shared,
            "link": metadata.get("webViewLink") if shared else None,
            "permission_id": public_permission.get("id") if shared else None,
        }

    def enable_share(self, file_id: str) -> Dict:
        """Enable public read sharing for a file and return link info."""
        service = self.get_service()
        try:
            current = self.get_share_status(file_id)
            if current.get("shared"):
                return current

            permission = service.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"},
                fields="id",
            ).execute()

            metadata = service.files().get(
                fileId=file_id,
                fields='id, webViewLink'
            ).execute()
        except HttpError as e:
            logger.error(f"Failed to enable share for {file_id}: {e}")
            raise

        return {
            "shared": True,
            "link": metadata.get("webViewLink"),
            "permission_id": permission.get("id"),
        }

    def disable_share(self, file_id: str, permission_id: Optional[str] = None) -> Dict:
        """Revoke public sharing for a file."""
        service = self.get_service()
        try:
            perm_id = permission_id
            if not perm_id:
                status = self.get_share_status(file_id)
                perm_id = status.get("permission_id")
            if perm_id:
                service.permissions().delete(fileId=file_id, permissionId=perm_id).execute()
        except HttpError as e:
            logger.error(f"Failed to revoke share for {file_id}: {e}")
            raise

        return {
            "shared": False,
            "link": None,
            "permission_id": None,
        }

    def get_thumbnail(self, file_id: str) -> Optional[bytes]:
        """
        Get thumbnail bytes for a video.
        Returns bytes or None if not available.
        """
        service = self.get_service()
        try:
            file_metadata = service.files().get(
                fileId=file_id,
                fields='thumbnailLink,hasThumbnail'
            ).execute()

            if not file_metadata.get('hasThumbnail'):
                return None

            thumbnail_link = file_metadata.get('thumbnailLink')
            if not thumbnail_link:
                return None

            # Download thumbnail
            token = self._get_access_token()
            headers = {'Authorization': f'Bearer {token}'}
            response = request_with_retry(
                "GET",
                thumbnail_link,
                headers=headers,
                timeout=(settings.DRIVE_HTTP_TIMEOUT_CONNECT, settings.DRIVE_HTTP_TIMEOUT_READ),
                retries=settings.DRIVE_HTTP_RETRIES,
                backoff=settings.DRIVE_HTTP_BACKOFF,
            )

            if response.status_code == 200:
                return response.content

            return None
        except Exception as e:
            logger.error(f"Error getting thumbnail for {file_id}: {e}")
            return None

    def get_image_file(self, file_id: str) -> Optional[tuple[bytes, str]]:
        """
        Download an image file directly from Drive.
        Returns tuple of (bytes, mime_type) or None if not available.
        Used for serving custom thumbnail files.
        """
        service = self.get_service()
        try:
            # Get file metadata to check mime type
            file_metadata = service.files().get(
                fileId=file_id,
                fields='mimeType, name, size'
            ).execute()

            mime_type = file_metadata.get('mimeType', 'image/jpeg')

            # Verify it's an image file
            if not mime_type.startswith('image/'):
                logger.warning(f"File {file_id} is not an image: {mime_type}")
                return None

            # Download the file
            token = self._get_access_token()
            headers = {'Authorization': f'Bearer {token}'}
            download_url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'
            response = request_with_retry(
                "GET",
                download_url,
                headers=headers,
                timeout=(settings.DRIVE_HTTP_TIMEOUT_CONNECT, settings.DRIVE_HTTP_TIMEOUT_READ),
                retries=settings.DRIVE_HTTP_RETRIES,
                backoff=settings.DRIVE_HTTP_BACKOFF,
            )

            if response.status_code == 200:
                return response.content, mime_type

            logger.warning(f"Failed to download image {file_id}: HTTP {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error getting image file {file_id}: {e}")
            return None


# Singleton instance
drive_manager = DriveManager()

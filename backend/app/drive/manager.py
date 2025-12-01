"""
Google Drive Manager - handles OAuth, uploads, downloads, and sync.
"""
from __future__ import annotations
import os
import threading
from pathlib import Path
from typing import Optional, List, Dict, Callable

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
import io
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from app.config import settings
from app.core.logging import get_module_logger
from app.core.thumbnail import ensure_thumbnail

logger = get_module_logger("drive")

SCOPES = ['https://www.googleapis.com/auth/drive.file']
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
        self._lock = threading.Lock()
        self._root_folder_id = None

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
            include_granted_scopes='true',
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
        with self._lock:
            if self._service is not None:
                return self._service

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

            self._service = build('drive', 'v3', credentials=creds)
            return self._service

    def get_or_create_root_folder(self) -> str:
        """Get or create the root 'YouTube Archiver' folder"""
        if self._root_folder_id:
            return self._root_folder_id

        service = self.get_service()

        # Search for existing folder
        query = f"name='{DRIVE_ROOT_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields='files(id, name)').execute()
        files = results.get('files', [])

        if files:
            self._root_folder_id = files[0]['id']
            return self._root_folder_id

        # Create folder
        folder_metadata = {
            'name': DRIVE_ROOT_FOLDER,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        self._root_folder_id = folder['id']
        return self._root_folder_id

    def ensure_folder(self, name: str, parent_id: str) -> str:
        """Ensure a folder exists, creating if necessary"""
        service = self.get_service()

        # Escape single quotes in folder name for query
        escaped_name = name.replace("'", "\\'")
        query = f"name='{escaped_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields='files(id)').execute()
        files = results.get('files', [])

        if files:
            return files[0]['id']

        # Create folder
        folder_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder['id']

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

            results = service.files().list(q=query, fields='files(id, name, size)').execute()
            existing_files = results.get('files', [])

            if existing_files:
                logger.debug(f"File already exists in Drive: {file_name}")
                return {
                    "status": "skipped",
                    "message": "File already exists in Drive",
                    "file_id": existing_files[0]['id'],
                    "file_name": file_name,
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
            media = MediaFileUpload(
                local_path,
                resumable=True,
                chunksize=8 * 1024 * 1024  # 8MB chunks
            )

            request = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size'
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status and progress_callback:
                    progress_callback({
                        "file_name": file_name,
                        "progress": int(status.progress() * 100)
                    })

            logger.info(f"Upload completed: {file_name} (ID: {response['id']})")

            uploaded_related = []
            # Upload related files
            for related_file in related_files:
                try:
                    # Check if already exists
                    escaped_related_name = related_file.name.replace("'", "\\'")
                    query = f"name='{escaped_related_name}' and '{current_parent}' in parents and trashed=false"
                    results = service.files().list(q=query, fields='files(id)').execute()
                    if results.get('files', []):
                        continue  # Already exists, skip

                    # Upload
                    related_metadata = {
                        'name': related_file.name,
                        'parents': [current_parent]
                    }
                    related_media = MediaFileUpload(str(related_file))
                    service.files().create(
                        body=related_metadata,
                        media_body=related_media,
                        fields='id, name'
                    ).execute()
                    uploaded_related.append(related_file.name)
                except Exception as e:
                    logger.warning(f"Failed to upload related file {related_file.name}: {e}")

            return {
                "status": "success",
                "file_id": response['id'],
                "file_name": response['name'],
                "size": response.get('size', 0),
                "related_files": uploaded_related,
                "thumbnail_generated": thumbnail_generated,
            }

        except Exception as e:
            logger.error(f"Exception in upload_video: {e}", exc_info=True)
            raise

    def list_videos(self) -> List[Dict]:
        """List all videos in the Drive folder"""
        service = self.get_service()
        root_id = self.get_or_create_root_folder()

        videos = []
        # Store thumbnails by folder_id and base_name for matching
        thumbnails_by_folder: Dict[str, Dict[str, Dict]] = {}

        def scan_folder(folder_id: str, path_prefix: str = ""):
            """Recursively scan a folder"""
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                fields='files(id, name, mimeType, size, createdTime, modifiedTime, thumbnailLink)',
                pageSize=1000
            ).execute()

            items = results.get('files', [])

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

                        # If no Drive thumbnail, look for custom thumbnail
                        if not drive_thumbnail and folder_id in thumbnails_by_folder:
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
                    results = service.files().list(q=query, fields='files(id)').execute()

                    if results.get('files', []):
                        logger.debug(f"File already exists, skipping: {file_name}")
                        uploaded_files.append({
                            "name": file_name,
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
                        media = MediaFileUpload(
                            str(file_path),
                            resumable=True,
                            chunksize=8 * 1024 * 1024
                        )

                        request = service.files().create(
                            body=file_metadata,
                            media_body=media,
                            fields='id, name, size'
                        )

                        response = None
                        while response is None:
                            status, response = request.next_chunk()
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
                    else:
                        media = MediaFileUpload(str(file_path))
                        response = service.files().create(
                            body=file_metadata,
                            media_body=media,
                            fields='id, name, size'
                        ).execute()

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
            service = self.get_service()

            # Get file metadata
            file_metadata = service.files().get(
                fileId=file_id,
                fields='name, size, mimeType'
            ).execute()

            file_name = file_metadata.get('name', 'unknown')
            file_size = int(file_metadata.get('size', 0))

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

            # Download file
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status and progress_callback:
                    progress_callback({
                        "file_name": file_name,
                        "progress": int(status.progress() * 100)
                    })

            # Write to file
            with open(local_path, 'wb') as f:
                fh.seek(0)
                f.write(fh.read())

            logger.info(f"Download completed: {file_name}")

            # Also download related files (thumbnails, metadata, subtitles)
            downloaded_related = self._download_related_files(
                file_id, file_name, local_path.parent
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
        video_file_id: str,
        video_name: str,
        local_dir: Path
    ) -> List[str]:
        """
        Download related files (thumbnails, metadata, subtitles) for a video.

        Args:
            video_file_id: The video file ID to find parent folder
            video_name: Video filename to match related files
            local_dir: Local directory to save files

        Returns:
            List of downloaded related file names
        """
        try:
            service = self.get_service()
            base_name = Path(video_name).stem

            # Get parent folder ID
            file_info = service.files().get(
                fileId=video_file_id,
                fields='parents'
            ).execute()

            parents = file_info.get('parents', [])
            if not parents:
                return []

            parent_id = parents[0]

            # Related file extensions
            related_extensions = [
                '.jpg', '.jpeg', '.png', '.webp',  # Thumbnails
                '.info.json',  # Metadata
                '.vtt', '.srt', '.ass',  # Subtitles
                '.description',  # Description
            ]

            # Search for related files in same folder
            escaped_base_name = base_name.replace("'", "\\'")
            query = f"'{parent_id}' in parents and name contains '{escaped_base_name}' and trashed=false"
            results = service.files().list(
                q=query,
                fields='files(id, name, size, mimeType)'
            ).execute()

            downloaded = []
            for item in results.get('files', []):
                item_name = item['name']
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
                        # Download related file
                        request = service.files().get_media(fileId=item['id'])
                        fh = io.BytesIO()
                        downloader = MediaIoBaseDownload(fh, request)

                        done = False
                        while not done:
                            _, done = downloader.next_chunk()

                        with open(local_file_path, 'wb') as f:
                            fh.seek(0)
                            f.write(fh.read())

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

    def get_file_metadata(self, file_id: str) -> Dict:
        """Get file metadata including size and mime type"""
        service = self.get_service()
        return service.files().get(
            fileId=file_id,
            fields='size, mimeType, name'
        ).execute()

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
            import requests
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            headers = {'Authorization': f'Bearer {creds.token}'}
            response = requests.get(thumbnail_link, headers=headers)

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
            import requests
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            headers = {'Authorization': f'Bearer {creds.token}'}
            download_url = f'https://www.googleapis.com/drive/v3/files/{file_id}?alt=media'

            response = requests.get(download_url, headers=headers)

            if response.status_code == 200:
                return response.content, mime_type

            logger.warning(f"Failed to download image {file_id}: HTTP {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error getting image file {file_id}: {e}")
            return None


# Singleton instance
drive_manager = DriveManager()

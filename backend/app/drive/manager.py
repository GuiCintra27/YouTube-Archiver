"""
Google Drive Manager - handles OAuth, uploads, downloads, and sync.
"""
from __future__ import annotations
import os
import threading
from pathlib import Path
from typing import Optional, List, Dict, Callable

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from app.config import settings

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
                    print(f"[DEBUG] Failed to refresh token: {e}")
                    return False

            return False
        except Exception as e:
            print(f"[DEBUG] Error checking authentication: {e}")
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

            print(f"[DEBUG] Uploading video: {file_name}")
            print(f"[DEBUG] Local path: {local_path}")

            # Check if video file already exists
            escaped_file_name = file_name.replace("'", "\\'")
            query = f"name='{escaped_file_name}' and '{current_parent}' in parents and trashed=false"
            print(f"[DEBUG] Query: {query}")

            results = service.files().list(q=query, fields='files(id, name, size)').execute()
            existing_files = results.get('files', [])

            if existing_files:
                print(f"[DEBUG] File already exists in Drive")
                return {
                    "status": "skipped",
                    "message": "File already exists in Drive",
                    "file_id": existing_files[0]['id'],
                    "file_name": file_name,
                }

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

            print(f"[DEBUG] Starting upload...")
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

            print(f"[DEBUG] Upload completed: {response['id']}")

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
                    print(f"Warning: Failed to upload related file {related_file.name}: {e}")

            return {
                "status": "success",
                "file_id": response['id'],
                "file_name": response['name'],
                "size": response.get('size', 0),
                "related_files": uploaded_related,
            }

        except Exception as e:
            import traceback
            print(f"[ERROR] Exception in upload_video: {e}")
            print(traceback.format_exc())
            raise

    def list_videos(self) -> List[Dict]:
        """List all videos in the Drive folder"""
        service = self.get_service()
        root_id = self.get_or_create_root_folder()

        videos = []

        def scan_folder(folder_id: str, path_prefix: str = ""):
            """Recursively scan a folder"""
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                fields='files(id, name, mimeType, size, createdTime, modifiedTime, thumbnailLink)',
                pageSize=1000
            ).execute()

            items = results.get('files', [])

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recurse into subfolders
                    new_path = f"{path_prefix}/{item['name']}" if path_prefix else item['name']
                    scan_folder(item['id'], new_path)
                else:
                    # It's a file
                    ext = Path(item['name']).suffix.lower()
                    if ext in settings.VIDEO_EXTENSIONS:
                        videos.append({
                            "id": item['id'],
                            "name": item['name'],
                            "path": f"{path_prefix}/{item['name']}" if path_prefix else item['name'],
                            "size": int(item.get('size', 0)),
                            "created_at": item.get('createdTime'),
                            "modified_at": item.get('modifiedTime'),
                            "thumbnail": item.get('thumbnailLink'),
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

    def delete_video(self, file_id: str) -> bool:
        """Remove a video from Drive"""
        service = self.get_service()
        try:
            service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
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
            print(f"Error getting thumbnail: {e}")
            return None


# Singleton instance
drive_manager = DriveManager()

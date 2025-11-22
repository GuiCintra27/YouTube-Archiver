"""
Módulo de gerenciamento do Google Drive.
Responsável por autenticação, listagem, upload e sincronização de vídeos.
"""
from __future__ import annotations
import os
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive.file']
DRIVE_ROOT_FOLDER = "YouTube Archiver"
SYNC_FILE_NAME = ".yt-archiver-sync.json"


class DriveManager:
    """Gerenciador do Google Drive com suporte a OAuth e sincronização"""

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
        """Gera URL de autenticação OAuth"""
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
        """Troca código de autorização por tokens"""
        flow = Flow.from_client_secrets_file(
            self.credentials_path,
            scopes=SCOPES,
            redirect_uri='http://localhost:8000/api/drive/oauth2callback'
        )

        flow.fetch_token(code=code)
        creds = flow.credentials

        # Salvar token
        with open(self.token_path, 'w') as token:
            token.write(creds.to_json())

        return {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        }

    def is_authenticated(self) -> bool:
        """Verifica se há token válido"""
        if not os.path.exists(self.token_path):
            return False

        try:
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            return creds and creds.valid
        except:
            return False

    def _get_service(self):
        """Obtém serviço autenticado do Google Drive"""
        with self._lock:
            if self._service is not None:
                return self._service

            creds = None
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    # Atualizar token salvo
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                else:
                    raise Exception("Not authenticated. Please authenticate first.")

            self._service = build('drive', 'v3', credentials=creds)
            return self._service

    def get_or_create_root_folder(self) -> str:
        """Obtém ou cria a pasta raiz 'YouTube Archiver'"""
        if self._root_folder_id:
            return self._root_folder_id

        service = self._get_service()

        # Buscar pasta existente
        query = f"name='{DRIVE_ROOT_FOLDER}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, fields='files(id, name)').execute()
        files = results.get('files', [])

        if files:
            self._root_folder_id = files[0]['id']
            return self._root_folder_id

        # Criar pasta
        folder_metadata = {
            'name': DRIVE_ROOT_FOLDER,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        self._root_folder_id = folder['id']
        return self._root_folder_id

    def ensure_folder(self, name: str, parent_id: str) -> str:
        """Garante que uma pasta existe, criando se necessário"""
        service = self._get_service()

        # Buscar pasta existente
        # Escapar aspas simples no nome da pasta para a query
        escaped_name = name.replace("'", "\\'")
        query = f"name='{escaped_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields='files(id)').execute()
        files = results.get('files', [])

        if files:
            return files[0]['id']

        # Criar pasta
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
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Faz upload de um vídeo para o Drive mantendo estrutura de pastas.
        Também faz upload de arquivos relacionados (thumbnails, metadata, legendas).

        Args:
            local_path: Caminho completo do arquivo local
            relative_path: Caminho relativo a partir de downloads/ (ex: "Canal/Video.mp4")
            progress_callback: Callback para reportar progresso
        """
        try:
            service = self._get_service()
            root_id = self.get_or_create_root_folder()

            # Criar estrutura de pastas
            path_parts = Path(relative_path).parts
            current_parent = root_id

            # Criar todas as pastas intermediárias
            for folder_name in path_parts[:-1]:
                current_parent = self.ensure_folder(folder_name, current_parent)

            # Nome do arquivo de vídeo
            file_name = path_parts[-1]
            video_path = Path(local_path)
            base_name = video_path.stem

            print(f"[DEBUG] Uploading video: {file_name}")
            print(f"[DEBUG] Local path: {local_path}")

            # Verificar se arquivo de vídeo já existe
            # Escapar aspas simples no nome do arquivo para a query
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

            # Procurar arquivos relacionados (thumbnail, metadata, legendas)
            parent_dir = video_path.parent
            related_files = []

            # Extensões de arquivos relacionados para fazer upload
            related_extensions = [
                '.jpg', '.jpeg', '.png', '.webp',  # Thumbnails
                '.info.json',  # Metadata
                '.vtt', '.srt', '.ass',  # Legendas
                '.description',  # Descrição
            ]

            for file in parent_dir.iterdir():
                if file.is_file() and file != video_path:
                    # Verificar se é um arquivo relacionado ao vídeo
                    if file.name.startswith(base_name + "."):
                        # Verificar se tem extensão relevante
                        if any(file.name.endswith(ext) for ext in related_extensions):
                            related_files.append(file)

            # Upload do vídeo principal
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
            # Upload de arquivos relacionados
            for related_file in related_files:
                try:
                    # Verificar se já existe
                    # Escapar aspas simples no nome do arquivo para a query
                    escaped_related_name = related_file.name.replace("'", "\\'")
                    query = f"name='{escaped_related_name}' and '{current_parent}' in parents and trashed=false"
                    results = service.files().list(q=query, fields='files(id)').execute()
                    if results.get('files', []):
                        continue  # Já existe, pular

                    # Fazer upload
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
        """Lista todos os vídeos na pasta do Drive"""
        service = self._get_service()
        root_id = self.get_or_create_root_folder()

        videos = []

        def scan_folder(folder_id: str, path_prefix: str = ""):
            """Escaneia recursivamente uma pasta"""
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                fields='files(id, name, mimeType, size, createdTime, modifiedTime, thumbnailLink)',
                pageSize=1000
            ).execute()

            items = results.get('files', [])

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Recursão em subpastas
                    new_path = f"{path_prefix}/{item['name']}" if path_prefix else item['name']
                    scan_folder(item['id'], new_path)
                else:
                    # É um arquivo
                    # Filtrar apenas vídeos
                    ext = Path(item['name']).suffix.lower()
                    if ext in {'.mp4', '.mkv', '.webm', '.avi', '.mov'}:
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
        Compara estado local vs Drive e retorna diferenças.

        Returns:
            {
                "local_only": [...],  # Vídeos apenas locais
                "drive_only": [...],  # Vídeos apenas no Drive
                "synced": [...],      # Vídeos em ambos
            }
        """
        # Listar vídeos locais
        local_videos = set()
        base_path = Path(local_base_dir)

        if base_path.exists():
            for video_file in base_path.rglob('*'):
                if video_file.suffix.lower() in {'.mp4', '.mkv', '.webm', '.avi', '.mov'}:
                    rel_path = video_file.relative_to(base_path)
                    local_videos.add(str(rel_path))

        # Listar vídeos no Drive
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
        """Remove um vídeo do Drive"""
        service = self._get_service()
        try:
            service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def get_file_stream(self, file_id: str):
        """
        Retorna um stream de download de um arquivo.
        Para usar com MediaIoBaseDownload ou streaming direto.
        """
        service = self._get_service()
        request = service.files().get_media(fileId=file_id)
        return request

    def get_thumbnail(self, file_id: str) -> Optional[bytes]:
        """
        Obtém a thumbnail de um vídeo do Drive.
        Retorna bytes da imagem ou None se não houver.
        """
        service = self._get_service()
        try:
            # Obter metadados do arquivo incluindo thumbnailLink
            file_metadata = service.files().get(
                fileId=file_id,
                fields='thumbnailLink,hasThumbnail'
            ).execute()

            if not file_metadata.get('hasThumbnail'):
                return None

            thumbnail_link = file_metadata.get('thumbnailLink')
            if not thumbnail_link:
                return None

            # Download da thumbnail
            import requests
            # Usar as credenciais para fazer o request
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            headers = {'Authorization': f'Bearer {creds.token}'}
            response = requests.get(thumbnail_link, headers=headers)

            if response.status_code == 200:
                return response.content

            return None
        except Exception as e:
            print(f"Error getting thumbnail: {e}")
            return None

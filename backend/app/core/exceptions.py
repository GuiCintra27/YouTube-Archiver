"""
Custom exceptions for the application.

All exceptions use standardized error codes for consistent API responses.
"""
from fastapi import status

from .errors import AppException, ErrorCode


class VideoNotFoundException(AppException):
    """Raised when a video is not found"""
    def __init__(self, detail: str = "Vídeo não encontrado", path: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.VIDEO_NOT_FOUND,
            message=detail,
            details={"path": path} if path else None,
        )


class ThumbnailNotFoundException(AppException):
    """Raised when a thumbnail is not found"""
    def __init__(self, detail: str = "Thumbnail não encontrada", path: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.THUMBNAIL_NOT_FOUND,
            message=detail,
            details={"path": path} if path else None,
        )


class JobNotFoundException(AppException):
    """Raised when a job is not found"""
    def __init__(self, detail: str = "Job não encontrado", job_id: str = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.JOB_NOT_FOUND,
            message=detail,
            details={"job_id": job_id} if job_id else None,
        )


class AccessDeniedException(AppException):
    """Raised when access to a resource is denied"""
    def __init__(self, detail: str = "Acesso negado", path: str = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.ACCESS_DENIED,
            message=detail,
            details={"path": path} if path else None,
        )


class InvalidRequestException(AppException):
    """Raised when a request is invalid"""
    def __init__(self, detail: str = "Requisição inválida", field: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.INVALID_REQUEST,
            message=detail,
            details={"field": field} if field else None,
        )


class DriveNotAuthenticatedException(AppException):
    """Raised when Google Drive is not authenticated"""
    def __init__(self, detail: str = "Not authenticated with Google Drive"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.DRIVE_NOT_AUTHENTICATED,
            message=detail,
        )


class DriveCredentialsNotFoundException(AppException):
    """Raised when Google Drive credentials file is not found"""
    def __init__(
        self,
        detail: str = "Credentials file not found. Please add credentials.json to the backend folder."
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.FILE_NOT_FOUND,
            message=detail,
            details={"file": "credentials.json"},
        )


class RangeNotSatisfiableException(AppException):
    """Raised when a range request cannot be satisfied"""
    def __init__(self, detail: str = "Range not satisfiable", file_size: int = None):
        super().__init__(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            error_code=ErrorCode.RANGE_NOT_SATISFIABLE,
            message=detail,
            details={"file_size": file_size} if file_size else None,
        )


class InvalidRangeHeaderException(AppException):
    """Raised when a range header is invalid"""
    def __init__(self, detail: str = "Invalid range header", header: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.INVALID_RANGE_HEADER,
            message=detail,
            details={"header": header} if header else None,
        )


class DownloadFailedException(AppException):
    """Raised when a download fails"""
    def __init__(self, detail: str = "Download failed", url: str = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.DOWNLOAD_FAILED,
            message=detail,
            details={"url": url} if url else None,
        )


class UploadFailedException(AppException):
    """Raised when an upload to Drive fails"""
    def __init__(self, detail: str = "Upload failed", file_name: str = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.UPLOAD_FAILED,
            message=detail,
            details={"file_name": file_name} if file_name else None,
        )


class PathTraversalException(AppException):
    """Raised when path traversal is detected"""
    def __init__(self, detail: str = "Path traversal not allowed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.PATH_TRAVERSAL,
            message=detail,
        )

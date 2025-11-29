"""
Custom exceptions for the application
"""
from fastapi import HTTPException, status


class VideoNotFoundException(HTTPException):
    """Raised when a video is not found"""
    def __init__(self, detail: str = "Vídeo não encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ThumbnailNotFoundException(HTTPException):
    """Raised when a thumbnail is not found"""
    def __init__(self, detail: str = "Thumbnail não encontrada"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class JobNotFoundException(HTTPException):
    """Raised when a job is not found"""
    def __init__(self, detail: str = "Job não encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AccessDeniedException(HTTPException):
    """Raised when access to a resource is denied"""
    def __init__(self, detail: str = "Acesso negado"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class InvalidRequestException(HTTPException):
    """Raised when a request is invalid"""
    def __init__(self, detail: str = "Requisição inválida"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class DriveNotAuthenticatedException(HTTPException):
    """Raised when Google Drive is not authenticated"""
    def __init__(self, detail: str = "Not authenticated with Google Drive"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class DriveCredentialsNotFoundException(HTTPException):
    """Raised when Google Drive credentials file is not found"""
    def __init__(self, detail: str = "Credentials file not found. Please add credentials.json to the backend folder."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class RangeNotSatisfiableException(HTTPException):
    """Raised when a range request cannot be satisfied"""
    def __init__(self, detail: str = "Range not satisfiable"):
        super().__init__(status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, detail=detail)


class InvalidRangeHeaderException(HTTPException):
    """Raised when a range header is invalid"""
    def __init__(self, detail: str = "Invalid range header"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

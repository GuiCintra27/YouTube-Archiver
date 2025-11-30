"""
Standardized error handling for the application.

Provides consistent error codes, response models, and exception handlers
for uniform API error responses.
"""
from typing import Any, Optional
from pydantic import BaseModel
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.logging import get_module_logger

logger = get_module_logger("errors")


# =============================================================================
# Error Codes
# =============================================================================

class ErrorCode:
    """
    Standardized error codes for the API.

    Format: CATEGORY_SPECIFIC_ERROR
    Categories: VALIDATION, AUTH, DOWNLOAD, JOB, LIBRARY, DRIVE, SYSTEM
    """

    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_URL = "INVALID_URL"
    INVALID_PATH = "INVALID_PATH"
    INVALID_FILENAME = "INVALID_FILENAME"
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_RANGE_HEADER = "INVALID_RANGE_HEADER"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"

    # Authentication errors (401)
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    DRIVE_NOT_AUTHENTICATED = "DRIVE_NOT_AUTHENTICATED"

    # Authorization errors (403)
    ACCESS_DENIED = "ACCESS_DENIED"

    # Not found errors (404)
    NOT_FOUND = "NOT_FOUND"
    VIDEO_NOT_FOUND = "VIDEO_NOT_FOUND"
    THUMBNAIL_NOT_FOUND = "THUMBNAIL_NOT_FOUND"
    JOB_NOT_FOUND = "JOB_NOT_FOUND"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"

    # Conflict errors (409)
    JOB_ALREADY_EXISTS = "JOB_ALREADY_EXISTS"
    JOB_ALREADY_CANCELLED = "JOB_ALREADY_CANCELLED"

    # Range errors (416)
    RANGE_NOT_SATISFIABLE = "RANGE_NOT_SATISFIABLE"

    # Rate limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Server errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    UPLOAD_FAILED = "UPLOAD_FAILED"
    DRIVE_ERROR = "DRIVE_ERROR"


# =============================================================================
# Error Response Model
# =============================================================================

class ErrorResponse(BaseModel):
    """
    Standardized error response model.

    All API errors return this format for consistent client handling.
    """
    error_code: str
    message: str
    details: Optional[Any] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "VIDEO_NOT_FOUND",
                "message": "The requested video was not found",
                "details": {"path": "videos/example.mp4"}
            }
        }


class ErrorDetail(BaseModel):
    """Detailed error information for validation errors"""
    field: str
    message: str
    type: str


# =============================================================================
# Custom Application Exception
# =============================================================================

class AppException(HTTPException):
    """
    Base application exception with error code support.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Any] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(status_code=status_code, detail=message)


# =============================================================================
# Helper Functions
# =============================================================================

def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Any] = None,
) -> JSONResponse:
    """
    Create a standardized JSON error response.

    Args:
        status_code: HTTP status code
        error_code: Application error code
        message: Human-readable error message
        details: Additional error details

    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=message,
            details=details,
        ).model_dump(),
    )


def raise_error(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Any] = None,
) -> None:
    """
    Raise an AppException with the given parameters.

    Args:
        status_code: HTTP status code
        error_code: Application error code
        message: Human-readable error message
        details: Additional error details

    Raises:
        AppException: Always raises
    """
    raise AppException(
        status_code=status_code,
        error_code=error_code,
        message=message,
        details=details,
    )


# =============================================================================
# Exception Handlers
# =============================================================================

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle AppException and return standardized error response.
    """
    logger.warning(
        f"AppException: {exc.error_code} - {exc.message}",
        extra={"details": exc.details, "path": request.url.path}
    )

    return create_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle standard HTTPException and return standardized error response.
    """
    # Map status codes to error codes
    error_code_map = {
        400: ErrorCode.INVALID_REQUEST,
        401: ErrorCode.NOT_AUTHENTICATED,
        403: ErrorCode.ACCESS_DENIED,
        404: ErrorCode.NOT_FOUND,
        416: ErrorCode.RANGE_NOT_SATISFIABLE,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={"path": request.url.path}
    )

    return create_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail),
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors and return standardized error response.
    """
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(ErrorDetail(
            field=field,
            message=error["msg"],
            type=error["type"],
        ).model_dump())

    logger.warning(
        f"Validation error: {len(errors)} errors",
        extra={"errors": errors, "path": request.url.path}
    )

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Validation error in request",
        details={"errors": errors},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions and return standardized error response.
    """
    logger.error(
        f"Unhandled exception: {type(exc).__name__} - {exc}",
        exc_info=True,
        extra={"path": request.url.path}
    )

    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred",
        details={"type": type(exc).__name__} if logger.level <= 10 else None,  # DEBUG level
    )


# =============================================================================
# Registration Function
# =============================================================================

def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    # Uncomment to catch all unhandled exceptions (may hide useful errors in dev)
    # app.add_exception_handler(Exception, generic_exception_handler)

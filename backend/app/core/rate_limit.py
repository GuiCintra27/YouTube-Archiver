"""
Rate limiting configuration for the API.

Uses slowapi to limit request rates and prevent abuse.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.errors import ErrorCode, ErrorResponse


def get_client_ip(request: Request) -> str:
    """
    Get the client IP address from the request.

    Handles proxy headers (X-Forwarded-For) for accurate IP detection.
    """
    # Check for proxy headers first
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded.split(",")[0].strip()

    # Check for real IP header (used by some proxies)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fall back to direct connection IP
    return get_remote_address(request)


# Create the limiter instance
limiter = Limiter(key_func=get_client_ip)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.

    Returns a standardized error response.
    """
    # Extract limit info from the exception
    retry_after = exc.detail.split("per ")[1] if "per " in exc.detail else "later"

    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Too many requests. Please slow down.",
            details={
                "limit": exc.detail,
                "retry_after": retry_after,
            }
        ).model_dump(),
        headers={"Retry-After": retry_after},
    )


# =============================================================================
# Rate Limit Presets
# =============================================================================

class RateLimits:
    """
    Predefined rate limits for different endpoint types.

    Format: "X per Y" where Y is: second, minute, hour, day
    """

    # Download operations (resource intensive)
    DOWNLOAD_START = "10/minute"      # Starting new downloads
    DOWNLOAD_BATCH = "2/minute"       # Batch/sync operations

    # Read operations (lighter)
    LIST_VIDEOS = "60/minute"         # Listing videos
    GET_STATUS = "120/minute"         # Getting job/auth status
    STREAM_VIDEO = "30/minute"        # Video streaming requests

    # Write operations
    UPLOAD = "5/minute"               # Upload to Drive
    DELETE = "20/minute"              # Delete operations

    # Auth operations
    AUTH = "10/minute"                # OAuth operations

    # General API
    DEFAULT = "100/minute"            # Default for unspecified endpoints


def setup_rate_limiting(app) -> None:
    """
    Configure rate limiting for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Store limiter in app state
    app.state.limiter = limiter

    # Add the rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

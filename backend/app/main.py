"""
YT-Archiver API - Main application entry point
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging, logger
from app.core.errors import register_exception_handlers
from app.core.rate_limit import setup_rate_limiting
from app.core.middleware.request_id import RequestIdMiddleware
from app.core.middleware.metrics import MetricsMiddleware
from app.core.schemas import HealthResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Import routers
from app.downloads.router import router as downloads_router
from app.jobs.router import router as jobs_router
from app.library.router import router as library_router
from app.recordings.router import router as recordings_router
from app.drive.router import router as drive_router
from app.catalog.router import router as catalog_router

# Import background tasks
from app.jobs.cleanup import run_cleanup_loop
from app.drive.cache import (
    run_cache_sync_loop,
    initialize_cache_on_startup,
    shutdown_cache,
)

# Configure logging with settings
setup_logging(level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    cleanup_task = None
    cache_sync_task = None

    if settings.start_background_tasks:
        logger.info("Starting background tasks...")

        # Initialize Drive cache database
        await initialize_cache_on_startup()

        # Start job cleanup task (runs every 30 minutes)
        cleanup_task = asyncio.create_task(run_cleanup_loop(interval_minutes=30))

        # Start Drive cache sync task (runs at configured interval)
        cache_sync_task = asyncio.create_task(
            run_cache_sync_loop(interval_minutes=settings.DRIVE_CACHE_SYNC_INTERVAL)
        )
    else:
        logger.info("Background tasks disabled for WORKER_ROLE=api")

    yield

    # Shutdown
    if cleanup_task or cache_sync_task:
        logger.info("Shutting down background tasks...")

        if cleanup_task:
            cleanup_task.cancel()
        if cache_sync_task:
            cache_sync_task.cancel()

        try:
            if cleanup_task:
                await cleanup_task
        except asyncio.CancelledError:
            pass

        try:
            if cache_sync_task:
                await cache_sync_task
        except asyncio.CancelledError:
            pass

        # Close cache database
        await shutdown_cache()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para download e gerenciamento de vídeos do YouTube",
    lifespan=lifespan,
)

# Request correlation
app.add_middleware(RequestIdMiddleware)

# Metrics middleware
if settings.METRICS_ENABLED:
    app.add_middleware(MetricsMiddleware, exclude_paths={"/metrics"})

# Register exception handlers for standardized error responses
register_exception_handlers(app)

# Setup rate limiting
setup_rate_limiting(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(downloads_router)
app.include_router(jobs_router)
app.include_router(library_router)
app.include_router(recordings_router)
app.include_router(drive_router)
app.include_router(catalog_router)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.METRICS_ENABLED:
        return {"detail": "Metrics disabled"}
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION
    }


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Basic health check with runtime details."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "worker_role": settings.WORKER_ROLE,
        "catalog_enabled": settings.CATALOG_ENABLED,
        "metrics_enabled": settings.METRICS_ENABLED,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)

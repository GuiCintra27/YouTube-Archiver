"""
YT-Archiver API - Main application entry point
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging, logger
from app.core.errors import register_exception_handlers

# Import routers
from app.downloads.router import router as downloads_router
from app.jobs.router import router as jobs_router
from app.library.router import router as library_router
from app.recordings.router import router as recordings_router
from app.drive.router import router as drive_router

# Import background tasks
from app.jobs.cleanup import run_cleanup_loop

# Configure logging with settings
setup_logging(level=settings.LOG_LEVEL)
logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting background tasks...")
    cleanup_task = asyncio.create_task(run_cleanup_loop(interval_minutes=30))

    yield

    # Shutdown
    logger.info("Shutting down background tasks...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para download e gerenciamento de vídeos do YouTube",
    lifespan=lifespan,
)

# Register exception handlers for standardized error responses
register_exception_handlers(app)

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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)

"""
YT-Archiver API - Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging, logger

# Import routers
from app.downloads.router import router as downloads_router
from app.jobs.router import router as jobs_router
from app.library.router import router as library_router
from app.recordings.router import router as recordings_router
from app.drive.router import router as drive_router

# Configure logging with settings
setup_logging(level=settings.LOG_LEVEL)
logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para download e gerenciamento de vídeos do YouTube",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
    uvicorn.run(app, host="0.0.0.0", port=8000)

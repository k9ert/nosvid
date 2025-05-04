"""
FastAPI application for nosvid
"""

from fastapi import FastAPI

# Import routers
from .routers import platforms, statistics, videos
from .status import router as status_router

# Create FastAPI application
app = FastAPI(
    title="NosVid API",
    version="1.0.0",
    description="API for managing YouTube videos with NosVid",
    openapi_tags=[
        {"name": "videos", "description": "Operations with videos"},
        {"name": "platforms", "description": "Platform-specific operations"},
        {"name": "status", "description": "Status and scheduled jobs"},
        {"name": "statistics", "description": "Repository statistics"},
    ],
)

# Include routers
app.include_router(videos.router, prefix="/videos", tags=["videos"])
app.include_router(platforms.router, prefix="/videos", tags=["platforms"])
app.include_router(status_router, prefix="/status", tags=["status"])
app.include_router(statistics.router, prefix="/statistics", tags=["statistics"])

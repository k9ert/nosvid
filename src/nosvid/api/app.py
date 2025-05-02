"""
FastAPI application for nosvid
"""

from fastapi import FastAPI

# Import routers
from .routers import videos, platforms, download, statistics
from .status import router as status_router

# Create FastAPI application
app = FastAPI(
    title="NosVid API",
    version="1.0.0",
    description="API for managing YouTube videos with NosVid",
    openapi_tags=[
        {"name": "videos", "description": "Operations with videos"},
        {"name": "platforms", "description": "Platform-specific operations"},
        {"name": "download", "description": "Download operations"},
        {"name": "status", "description": "Status and scheduled jobs"},
        {"name": "statistics", "description": "Repository statistics"}
    ]
)

# Include routers
app.include_router(videos.router, prefix="/videos", tags=["videos"])
app.include_router(platforms.router, prefix="/videos", tags=["platforms"])
app.include_router(download.router, prefix="/download", tags=["download"])
app.include_router(status_router, prefix="/status", tags=["status"])
app.include_router(statistics.router, prefix="/statistics", tags=["statistics"])

# Add backward compatibility endpoint for /videos/{video_id}/download
from fastapi import Depends, HTTPException
from datetime import datetime
from .dependencies import get_video_service, get_channel_title
from .models import DownloadRequest, DownloadResponse
from ..services.video_service import VideoService

@app.post("/videos/{video_id}/download", response_model=DownloadResponse, tags=["videos"], deprecated=True)
def download_video(
    video_id: str,
    request: DownloadRequest,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Download a video (deprecated, use /videos/{video_id}/platforms/youtube/download instead)
    """
    # Generate a simple user identifier (in a real app, this would be a session ID or user ID)
    user_id = f"user-{datetime.now().timestamp()}"

    result = video_service.download_video(video_id, channel_title, request.quality, user_id)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "message": f"Video {video_id} downloaded successfully from YouTube"
    }



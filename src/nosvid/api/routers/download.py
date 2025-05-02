"""
Download API endpoints
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ...services.video_service import VideoService, download_status
from ..dependencies import get_video_service, get_channel_title
from ..models import DownloadRequest, DownloadResponse, DownloadStatusResponse

# Create router
router = APIRouter()


@router.get("/status", response_model=DownloadStatusResponse)
def get_download_status():
    """
    Get the current download status
    """
    return download_status


# Keep the old endpoint for backward compatibility, but mark it as deprecated
@router.post("/{video_id}", response_model=DownloadResponse, deprecated=True)
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

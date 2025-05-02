"""
Statistics API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ...services.video_service import VideoService
from ..dependencies import get_video_service, get_channel_title
from ..models import StatisticsResponse

# Create router
router = APIRouter()


@router.get("", response_model=StatisticsResponse)
def get_statistics(
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Get repository statistics
    """
    result = video_service.get_cache_statistics(channel_title)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return result.data

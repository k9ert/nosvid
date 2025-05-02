"""
Videos API endpoints
"""

import os
import glob
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import RedirectResponse, FileResponse
from typing import List, Optional, Dict, Any

from ...services.video_service import VideoService
from ...utils.filesystem import get_video_dir, get_platform_dir, load_json_file, load_text_file
from ...platforms.youtube import find_youtube_video_file
from ..dependencies import get_video_service, get_channel_title
from ..models import (
    VideoResponse, VideoListResponse, DownloadRequest, DownloadResponse,
    NostrmediaUploadRequest, NostrmediaUrlRequest, UpdateMetadataRequest,
    PlatformResponse
)

# Create router
router = APIRouter()


@router.get("", response_model=VideoListResponse)
def list_videos(
    limit: Optional[int] = Query(None, description="Maximum number of videos to return"),
    offset: int = Query(0, description="Number of videos to skip"),
    sort_by: str = Query("published_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order ('asc' or 'desc')"),
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    List videos with pagination and sorting
    """
    # First, get the total count of videos without pagination
    total_result = video_service.list_videos(
        channel_title=channel_title,
        limit=None,
        offset=0,
        sort_by=sort_by,
        sort_order=sort_order
    )

    if not total_result.success:
        raise HTTPException(status_code=500, detail=total_result.error)

    total_count = len(total_result.data)

    # Then, get the paginated videos
    result = video_service.list_videos(
        channel_title=channel_title,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    videos = result.data

    # Process videos to ensure NostrPost objects are converted to dictionaries
    processed_videos = []
    for video in videos:
        # Extract nostr_posts and convert them to dictionaries
        nostr_posts = [post.to_dict() for post in video.nostr_posts]

        # Create a copy of the video with nostr_posts as dictionaries
        video_dict = {
            "video_id": video.video_id,
            "title": video.title,
            "published_at": video.published_at,
            "duration": video.duration,
            "platforms": {name: platform.to_dict() for name, platform in (video.platforms or {}).items()},
            "nostr_posts": nostr_posts,
            "npubs": video.npubs or {},
            "synced_at": video.synced_at
        }
        processed_videos.append(video_dict)

    return {
        "videos": processed_videos,
        "total": total_count,
        "offset": offset,
        "limit": limit
    }


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: str,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Get a video by ID
    """
    result = video_service.get_video(video_id, channel_title)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    if result.data is None:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    video = result.data

    # Process video to ensure NostrPost objects are converted to dictionaries
    nostr_posts = [post.to_dict() for post in video.nostr_posts]

    # Create a copy of the video with nostr_posts as dictionaries
    video_dict = {
        "video_id": video.video_id,
        "title": video.title,
        "published_at": video.published_at,
        "duration": video.duration,
        "platforms": {name: platform.to_dict() for name, platform in (video.platforms or {}).items()},
        "nostr_posts": nostr_posts,
        "npubs": video.npubs or {},
        "synced_at": video.synced_at
    }

    return video_dict


@router.post("/{video_id}/update-metadata", response_model=DownloadResponse)
def update_video_metadata(
    video_id: str,
    request: UpdateMetadataRequest,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Update metadata for a video

    This endpoint allows updating video metadata from external sources like DecData peers.
    It will merge the provided metadata with existing metadata, preserving local data when in conflict.
    """
    # First, check if the video exists
    video_result = video_service.get_video(video_id, channel_title)

    if not video_result.success:
        # If there's an error getting the video, try to create it
        if request.title:  # Only create if we have at least a title
            # Create a minimal video entry
            create_result = video_service.create_or_update_metadata(
                video_id=video_id,
                channel_title=channel_title,
                title=request.title,
                published_at=request.published_at,
                duration=request.duration or 0
            )

            if not create_result.success:
                raise HTTPException(status_code=500, detail=create_result.error)

            # Now get the newly created video
            video_result = video_service.get_video(video_id, channel_title)
            if not video_result.success:
                raise HTTPException(status_code=500, detail=video_result.error)
        else:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found and insufficient data to create it")

    video = video_result.data
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Update the video with the provided metadata
    # We'll implement the merge logic in the video service
    metadata_dict = {k: v for k, v in request.model_dump().items() if v is not None}
    result = video_service.update_metadata(
        video_id=video_id,
        channel_title=channel_title,
        metadata=metadata_dict  # Only include fields that were provided
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "message": f"Metadata updated successfully for video {video_id}"
    }


@router.get("/{video_id}/mp4")
def get_video_mp4(
    video_id: str,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Get the MP4 video file

    This endpoint will:
    - Return a redirect to the nostrmedia URL if available
    - Return the local MP4 file if available
    - Return a 404 if neither is available
    """
    # First, check if the video exists
    video_result = video_service.get_video(video_id, channel_title)

    if not video_result.success:
        raise HTTPException(status_code=500, detail=video_result.error)

    video = video_result.data
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Check if the video has a nostrmedia URL
    if video.platforms and 'nostrmedia' in video.platforms and video.platforms['nostrmedia'].url:
        # Redirect to the nostrmedia URL
        return RedirectResponse(url=video.platforms['nostrmedia'].url)

    # If no nostrmedia URL, try to find the local file
    videos_dir = os.path.join(video_service.video_repository.base_dir, channel_title, "videos")
    video_dir = get_video_dir(videos_dir, video_id)

    # Find the video file
    video_file = find_youtube_video_file(video_dir)

    if video_file and os.path.exists(video_file):
        # Return the local file
        return FileResponse(
            path=video_file,
            filename=os.path.basename(video_file),
            media_type="video/mp4"
        )

    # If no file is found, return a 404
    raise HTTPException(
        status_code=404,
        detail=f"No MP4 file found for video {video_id}"
    )

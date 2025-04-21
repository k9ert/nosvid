"""
FastAPI application for nosvid
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from ..services.config_service import ConfigService
from ..services.video_service import VideoService, download_status
from ..services.scheduler_service import SchedulerService
from ..repo.video_repo import FileSystemVideoRepo
from ..models.video import Video, Platform, NostrPost

# Import routers
from .status import router as status_router

# Create FastAPI application
app = FastAPI(
    title="NosVid API",
    version="1.0.0",
    description="API for managing YouTube videos with NosVid",
    openapi_tags=[
        {"name": "videos", "description": "Operations with videos"},
        {"name": "status", "description": "Status and scheduled jobs"},
        {"name": "statistics", "description": "Repository statistics"}
    ]
)

# Include routers
app.include_router(status_router, prefix="/status", tags=["status"])

# Models for API
class NostrPostResponse(BaseModel):
    """Response model for a Nostr post"""
    event_id: str
    pubkey: str
    uploaded_at: str
    nostr_uri: Optional[str] = None
    links: Dict[str, str] = {}

class VideoResponse(BaseModel):
    """Response model for a video"""
    video_id: str
    title: str
    published_at: str
    duration: int
    platforms: Dict[str, Any]
    nostr_posts: List[NostrPostResponse] = []
    npubs: Dict[str, List[str]] = {}
    synced_at: Optional[str] = None

    class Config:
        """Configuration for the model"""
        from_attributes = True

class VideoListResponse(BaseModel):
    """Response model for a list of videos"""
    videos: List[VideoResponse]
    total: int
    offset: int
    limit: Optional[int] = None

class DownloadRequest(BaseModel):
    """Request model for downloading a video"""
    quality: str = "best"

class DownloadResponse(BaseModel):
    """Response model for downloading a video"""
    success: bool
    message: str

class NostrmediaUploadRequest(BaseModel):
    """Request model for uploading a video to nostrmedia"""
    private_key: Optional[str] = None
    debug: bool = False

class NostrmediaUrlRequest(BaseModel):
    """Request model for providing an existing nostrmedia URL"""
    url: str
    hash: Optional[str] = None
    uploaded_at: Optional[str] = None

class DownloadStatusResponse(BaseModel):
    """Response model for checking download status"""
    in_progress: bool
    video_id: Optional[str] = None
    started_at: Optional[str] = None
    user: Optional[str] = None

class StatisticsResponse(BaseModel):
    """Response model for statistics"""
    total_in_cache: int = 0
    total_with_metadata: int = 0
    total_downloaded: int = 0
    total_uploaded_nm: int = 0
    total_posted_nostr: int = 0
    total_with_npubs: int = 0
    total_npubs: int = 0

# Dependency injection
def get_config_service():
    """Get the configuration service"""
    return ConfigService()

def get_video_repository(config_service: ConfigService = Depends(get_config_service)):
    """Get the video repository"""
    output_dir = config_service.get_output_dir()
    return FileSystemVideoRepo(output_dir)

def get_video_service(video_repository: FileSystemVideoRepo = Depends(get_video_repository)):
    """Get the video service"""
    return VideoService(video_repository)

def get_channel_title(config_service: ConfigService = Depends(get_config_service)):
    """Get the channel title"""
    return config_service.get_channel_title()

# Routes
@app.get("/videos", response_model=VideoListResponse, tags=["videos"])
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

@app.get("/videos/{video_id}", response_model=VideoResponse, tags=["videos"])
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

@app.post("/videos/{video_id}/platforms/youtube/download", response_model=DownloadResponse, tags=["videos"])
def download_youtube_video(
    video_id: str,
    request: DownloadRequest,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Download a video from YouTube
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

# Keep the old endpoint for backward compatibility, but mark it as deprecated
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
    return download_youtube_video(video_id, request, channel_title, video_service)

@app.post("/videos/{video_id}/platforms/nostrmedia/upload", response_model=DownloadResponse, tags=["videos"])
def upload_to_nostrmedia(
    video_id: str,
    request: NostrmediaUploadRequest,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Upload a video to nostrmedia.com
    """
    # First, check if the video exists and has been downloaded
    video_result = video_service.get_video(video_id, channel_title)

    if not video_result.success:
        raise HTTPException(status_code=500, detail=video_result.error)

    video = video_result.data
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Check if the video has been downloaded from YouTube
    if 'youtube' not in video.platforms or not video.platforms['youtube'].downloaded:
        raise HTTPException(
            status_code=400,
            detail=f"Video {video_id} has not been downloaded from YouTube yet. Download it first."
        )

    # Upload to nostrmedia
    result = video_service.upload_to_nostrmedia(video_id, channel_title, request.private_key, request.debug)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "message": f"Video {video_id} uploaded successfully to nostrmedia.com"
    }

@app.post("/videos/{video_id}/platforms/nostrmedia", response_model=DownloadResponse, tags=["videos"])
def set_nostrmedia_url(
    video_id: str,
    request: NostrmediaUrlRequest,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Set an existing nostrmedia URL for a video
    """
    # First, check if the video exists
    video_result = video_service.get_video(video_id, channel_title)

    if not video_result.success:
        raise HTTPException(status_code=500, detail=video_result.error)

    video = video_result.data
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Set the nostrmedia URL
    result = video_service.set_nostrmedia_url(
        video_id,
        channel_title,
        request.url,
        request.hash,
        request.uploaded_at or datetime.now().isoformat()
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "message": f"Nostrmedia URL set successfully for video {video_id}"
    }

@app.get("/download/status", response_model=DownloadStatusResponse, tags=["videos"])
def get_download_status():
    """
    Get the current download status
    """
    return download_status

@app.get("/statistics", response_model=StatisticsResponse, tags=["statistics"])
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

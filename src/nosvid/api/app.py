"""
FastAPI application for nosvid
"""

import os
import glob

from fastapi import FastAPI, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from ..services.config_service import ConfigService
from ..services.video_service import VideoService, download_status
from ..services.scheduler_service import SchedulerService
from ..repo.video_repo import FileSystemVideoRepo
from ..models.video import Video, Platform, NostrPost
from ..utils.filesystem import get_video_dir, get_platform_dir, load_json_file

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

class UpdateMetadataRequest(BaseModel):
    """Request model for updating video metadata"""
    title: Optional[str] = None
    published_at: Optional[str] = None
    duration: Optional[int] = None
    platforms: Optional[Dict[str, Any]] = None
    nostr_posts: Optional[List[Dict[str, Any]]] = None
    npubs: Optional[Dict[str, List[str]]] = None
    synced_at: Optional[str] = None

class PlatformResponse(BaseModel):
    """Response model for platform-specific data"""
    name: str
    url: Optional[str] = None
    downloaded: Optional[bool] = None
    downloaded_at: Optional[str] = None
    uploaded: Optional[bool] = None
    uploaded_at: Optional[str] = None
    data: Dict[str, Any] = {}

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

@app.get("/videos/{video_id}/platforms/youtube", response_model=PlatformResponse, tags=["videos"])
def get_youtube_platform(
    video_id: str,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Get YouTube-specific data for a video
    """
    # Get the video
    result = video_service.get_video(video_id, channel_title)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    video = result.data
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Check if the video has YouTube platform data
    if 'youtube' not in video.platforms:
        # If not, create a minimal platform response with just the URL
        return {
            "name": "youtube",
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "downloaded": False,
            "data": {}
        }

    # Get the platform data
    platform = video.platforms['youtube']

    # Get additional data from the filesystem
    videos_dir = os.path.join(video_service.video_repository.base_dir, channel_title, "videos")
    video_dir = get_video_dir(videos_dir, video_id)
    youtube_dir = get_platform_dir(video_dir, 'youtube')

    additional_data = {}

    # Check if the youtube directory exists
    if os.path.exists(youtube_dir):
        # Check for info.json
        info_file = os.path.join(youtube_dir, 'info.json')
        if os.path.exists(info_file):
            try:
                info_data = load_json_file(info_file)
                additional_data['info'] = info_data
            except Exception as e:
                print(f"Error loading info.json: {e}")

        # Check for metadata.json
        metadata_file = os.path.join(youtube_dir, 'metadata.json')
        if os.path.exists(metadata_file):
            try:
                metadata = load_json_file(metadata_file)
                additional_data['metadata'] = metadata
            except Exception as e:
                print(f"Error loading metadata.json: {e}")

        # Check for video files
        video_files = glob.glob(os.path.join(youtube_dir, '*.mp4')) + \
                     glob.glob(os.path.join(youtube_dir, '*.webm')) + \
                     glob.glob(os.path.join(youtube_dir, '*.mkv'))

        if video_files:
            additional_data['video_files'] = [os.path.basename(f) for f in video_files]

    # Return the platform data
    return {
        "name": platform.name,
        "url": platform.url,
        "downloaded": platform.downloaded,
        "downloaded_at": platform.downloaded_at,
        "data": additional_data
    }

@app.post("/videos/{video_id}/update-metadata", response_model=DownloadResponse, tags=["videos"])
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
    metadata_dict = {k: v for k, v in request.dict().items() if v is not None}
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

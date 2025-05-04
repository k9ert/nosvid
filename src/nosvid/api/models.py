"""
API models for nosvid
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# Nostr models
class NostrPostResponse(BaseModel):
    """Response model for a Nostr post"""

    event_id: str
    pubkey: str
    uploaded_at: str
    nostr_uri: Optional[str] = None
    links: Dict[str, str] = {}


# Video models
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


class UpdateMetadataRequest(BaseModel):
    """Request model for updating video metadata"""

    title: Optional[str] = None
    published_at: Optional[str] = None
    duration: Optional[int] = None
    platforms: Optional[Dict[str, Any]] = None
    nostr_posts: Optional[List[Dict[str, Any]]] = None
    npubs: Optional[Dict[str, List[str]]] = None
    synced_at: Optional[str] = None


# Platform models
class PlatformResponse(BaseModel):
    """Response model for platform-specific data"""

    name: str
    url: Optional[str] = None
    downloaded: Optional[bool] = None
    downloaded_at: Optional[str] = None
    uploaded: Optional[bool] = None
    uploaded_at: Optional[str] = None
    data: Dict[str, Any] = {}


class YouTubePlatformData(BaseModel):
    """Model for YouTube platform data"""

    metadata: Optional[Dict[str, Any]] = None
    info: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    live_chat: Optional[Dict[str, Any]] = None
    subtitles: Optional[Dict[str, Dict[str, str]]] = None
    description_files: Optional[Dict[str, str]] = None
    info_files: Optional[Dict[str, Dict[str, Any]]] = None
    live_chat_files: Optional[Dict[str, Dict[str, Any]]] = None
    thumbnails: Optional[List[str]] = None
    video_files: Optional[List[str]] = None
    other_files: Optional[List[str]] = None


class YouTubePlatformRequest(BaseModel):
    """Request model for creating YouTube platform data"""

    url: str
    downloaded: bool = True
    downloaded_at: Optional[str] = None
    data: YouTubePlatformData


# Download models
class DownloadRequest(BaseModel):
    """Request model for downloading a video"""

    quality: str = "best"


class SyncMetadataRequest(BaseModel):
    """Request model for syncing metadata"""

    force_refresh: bool = False


class DownloadResponse(BaseModel):
    """Response model for downloading a video"""

    success: bool
    message: str


class DownloadStatusResponse(BaseModel):
    """Response model for checking download status"""

    in_progress: bool
    video_id: Optional[str] = None
    started_at: Optional[str] = None
    user: Optional[str] = None


# Nostrmedia models
class NostrmediaUploadRequest(BaseModel):
    """Request model for uploading a video to nostrmedia"""

    private_key: Optional[str] = None
    debug: bool = False


class NostrmediaUrlRequest(BaseModel):
    """Request model for providing an existing nostrmedia URL"""

    url: str
    hash: Optional[str] = None
    uploaded_at: Optional[str] = None


# Statistics models
class StatisticsResponse(BaseModel):
    """Response model for statistics"""

    total_in_cache: int = 0
    total_with_metadata: int = 0
    total_downloaded: int = 0
    total_uploaded_nm: int = 0
    total_posted_nostr: int = 0
    total_with_npubs: int = 0
    total_npubs: int = 0

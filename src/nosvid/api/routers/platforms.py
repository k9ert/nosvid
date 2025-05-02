"""
Platform-specific API endpoints
"""

import os
import glob
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ...services.video_service import VideoService
from ...utils.filesystem import get_video_dir, get_platform_dir, load_json_file, load_text_file
from ..dependencies import get_video_service, get_channel_title
from ..models import (
    DownloadRequest, DownloadResponse, NostrmediaUploadRequest,
    NostrmediaUrlRequest, PlatformResponse
)

# Create router
router = APIRouter()


@router.get("/{video_id}/platforms/youtube", response_model=PlatformResponse)
def get_youtube_platform(
    video_id: str,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service)
):
    """
    Get YouTube-specific data for a video
    
    Returns all data from the YouTube folder, including:
    - metadata.json content
    - description file content
    - info.json content
    - live chat content
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
    
    folder_data = {}
    
    # Check if the youtube directory exists
    if os.path.exists(youtube_dir):
        # Get metadata.json
        metadata_file = os.path.join(youtube_dir, 'metadata.json')
        folder_data['metadata'] = load_json_file(metadata_file, {})
        
        # Get info.json (look for any file ending with .info.json)
        info_files = glob.glob(os.path.join(youtube_dir, '*.info.json'))
        if info_files:
            # Use the first info file found
            folder_data['info'] = load_json_file(info_files[0], {})
            
            # If there are multiple info files, include them all
            if len(info_files) > 1:
                folder_data['info_files'] = {}
                for info_file in info_files:
                    filename = os.path.basename(info_file)
                    folder_data['info_files'][filename] = load_json_file(info_file, {})
        
        # Get description files
        description_files = glob.glob(os.path.join(youtube_dir, '*.description'))
        if description_files:
            # Use the first description file found
            folder_data['description'] = load_text_file(description_files[0], "")
            
            # If there are multiple description files, include them all
            if len(description_files) > 1:
                folder_data['description_files'] = {}
                for desc_file in description_files:
                    filename = os.path.basename(desc_file)
                    folder_data['description_files'][filename] = load_text_file(desc_file, "")
        
        # Get live chat files
        live_chat_files = glob.glob(os.path.join(youtube_dir, '*.live_chat.json'))
        if live_chat_files:
            # Use the first live chat file found
            folder_data['live_chat'] = load_json_file(live_chat_files[0], {})
            
            # If there are multiple live chat files, include them all
            if len(live_chat_files) > 1:
                folder_data['live_chat_files'] = {}
                for chat_file in live_chat_files:
                    filename = os.path.basename(chat_file)
                    folder_data['live_chat_files'][filename] = load_json_file(chat_file, {})
        
        # Get subtitle files
        subtitle_files = glob.glob(os.path.join(youtube_dir, '*.vtt')) + \
                         glob.glob(os.path.join(youtube_dir, '*.srt'))
        if subtitle_files:
            folder_data['subtitles'] = {}
            for sub_file in subtitle_files:
                filename = os.path.basename(sub_file)
                folder_data['subtitles'][filename] = load_text_file(sub_file, "")
        
        # Get thumbnail files
        thumbnail_files = glob.glob(os.path.join(youtube_dir, '*.jpg')) + \
                          glob.glob(os.path.join(youtube_dir, '*.png')) + \
                          glob.glob(os.path.join(youtube_dir, '*.webp'))
        if thumbnail_files:
            folder_data['thumbnails'] = [os.path.basename(f) for f in thumbnail_files]
        
        # Get video files (but don't include the content, just the filenames)
        video_files = glob.glob(os.path.join(youtube_dir, '*.mp4')) + \
                     glob.glob(os.path.join(youtube_dir, '*.webm')) + \
                     glob.glob(os.path.join(youtube_dir, '*.mkv'))
        if video_files:
            folder_data['video_files'] = [os.path.basename(f) for f in video_files]
        
        # Get any other files in the directory
        all_files = os.listdir(youtube_dir)
        known_extensions = ['.json', '.description', '.live_chat.json', '.vtt', '.srt', 
                           '.jpg', '.png', '.webp', '.mp4', '.webm', '.mkv']
        other_files = [f for f in all_files if not any(f.endswith(ext) for ext in known_extensions)]
        if other_files:
            folder_data['other_files'] = other_files
    
    # Return the platform data
    return {
        "name": platform.name,
        "url": platform.url,
        "downloaded": platform.downloaded,
        "downloaded_at": platform.downloaded_at,
        "data": folder_data
    }


@router.post("/{video_id}/platforms/youtube/download", response_model=DownloadResponse)
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


@router.post("/{video_id}/platforms/nostrmedia/upload", response_model=DownloadResponse)
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


@router.post("/{video_id}/platforms/nostrmedia", response_model=DownloadResponse)
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

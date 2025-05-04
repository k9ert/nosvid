"""
Platform-specific API endpoints
"""

import glob
import os
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ...services.video_service import VideoService
from ...utils.filesystem import (
    get_platform_dir,
    get_video_dir,
    load_json_file,
    load_text_file,
    save_json_file,
    save_text_file,
)
from ..dependencies import get_channel_title, get_video_service
from ..models import (
    DownloadRequest,
    DownloadResponse,
    NostrmediaUploadRequest,
    NostrmediaUrlRequest,
    PlatformResponse,
    SyncMetadataRequest,
    YouTubePlatformRequest,
)

# Create router
router = APIRouter()


@router.get("/{video_id}/platforms/youtube", response_model=PlatformResponse)
def get_youtube_platform(
    video_id: str,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service),
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
    if "youtube" not in video.platforms:
        # If not, create a minimal platform response with just the URL
        return {
            "name": "youtube",
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "downloaded": False,
            "data": {},
        }

    # Get the platform data
    platform = video.platforms["youtube"]

    # Get additional data from the filesystem
    videos_dir = os.path.join(
        video_service.video_repository.base_dir, channel_title, "videos"
    )
    video_dir = get_video_dir(videos_dir, video_id)
    youtube_dir = get_platform_dir(video_dir, "youtube")

    folder_data = {}

    # Check if the youtube directory exists
    if os.path.exists(youtube_dir):
        # Get metadata.json
        metadata_file = os.path.join(youtube_dir, "metadata.json")
        folder_data["metadata"] = load_json_file(metadata_file, {})

        # Get info.json (look for any file ending with .info.json)
        info_files = glob.glob(os.path.join(youtube_dir, "*.info.json"))
        if info_files:
            # Use the first info file found
            folder_data["info"] = load_json_file(info_files[0], {})

            # If there are multiple info files, include them all
            if len(info_files) > 1:
                folder_data["info_files"] = {}
                for info_file in info_files:
                    filename = os.path.basename(info_file)
                    folder_data["info_files"][filename] = load_json_file(info_file, {})

        # Get description files
        description_files = glob.glob(os.path.join(youtube_dir, "*.description"))
        if description_files:
            # Use the first description file found
            folder_data["description"] = load_text_file(description_files[0], "")

            # If there are multiple description files, include them all
            if len(description_files) > 1:
                folder_data["description_files"] = {}
                for desc_file in description_files:
                    filename = os.path.basename(desc_file)
                    folder_data["description_files"][filename] = load_text_file(
                        desc_file, ""
                    )

        # Get live chat files
        live_chat_files = glob.glob(os.path.join(youtube_dir, "*.live_chat.json"))
        if live_chat_files:
            # Use the first live chat file found
            folder_data["live_chat"] = load_json_file(live_chat_files[0], {})

            # If there are multiple live chat files, include them all
            if len(live_chat_files) > 1:
                folder_data["live_chat_files"] = {}
                for chat_file in live_chat_files:
                    filename = os.path.basename(chat_file)
                    folder_data["live_chat_files"][filename] = load_json_file(
                        chat_file, {}
                    )

        # Get subtitle files
        subtitle_files = glob.glob(os.path.join(youtube_dir, "*.vtt")) + glob.glob(
            os.path.join(youtube_dir, "*.srt")
        )
        if subtitle_files:
            folder_data["subtitles"] = {}
            for sub_file in subtitle_files:
                filename = os.path.basename(sub_file)
                folder_data["subtitles"][filename] = load_text_file(sub_file, "")

        # Get thumbnail files
        thumbnail_files = (
            glob.glob(os.path.join(youtube_dir, "*.jpg"))
            + glob.glob(os.path.join(youtube_dir, "*.png"))
            + glob.glob(os.path.join(youtube_dir, "*.webp"))
        )
        if thumbnail_files:
            folder_data["thumbnails"] = [os.path.basename(f) for f in thumbnail_files]

        # Get video files (but don't include the content, just the filenames)
        video_files = (
            glob.glob(os.path.join(youtube_dir, "*.mp4"))
            + glob.glob(os.path.join(youtube_dir, "*.webm"))
            + glob.glob(os.path.join(youtube_dir, "*.mkv"))
        )
        if video_files:
            folder_data["video_files"] = [os.path.basename(f) for f in video_files]

        # Get any other files in the directory
        all_files = os.listdir(youtube_dir)
        known_extensions = [
            ".json",
            ".description",
            ".live_chat.json",
            ".vtt",
            ".srt",
            ".jpg",
            ".png",
            ".webp",
            ".mp4",
            ".webm",
            ".mkv",
        ]
        other_files = [
            f for f in all_files if not any(f.endswith(ext) for ext in known_extensions)
        ]
        if other_files:
            folder_data["other_files"] = other_files

    # Return the platform data
    return {
        "name": platform.name,
        "url": platform.url,
        "downloaded": platform.downloaded,
        "downloaded_at": platform.downloaded_at,
        "data": folder_data,
    }


@router.post(
    "/{video_id}/platforms/youtube", response_model=DownloadResponse, tags=["platforms"]
)
def sync_youtube_metadata(
    video_id: str,
    request: SyncMetadataRequest = None,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Sync metadata for a video from YouTube

    This endpoint downloads metadata for a video from YouTube without downloading the actual video file.
    It creates or updates the YouTube platform data for the specified video.

    - **video_id**: The YouTube video ID
    - **request**: Optional JSON payload with a force_refresh flag to force refresh from YouTube API

    If no request body is provided, it will use default settings.

    Returns a success message if the metadata was successfully synced.
    """
    # Default to an empty request if none is provided
    if request is None:
        request = SyncMetadataRequest()

    # Call the sync_youtube_metadata method from the video service
    from ...metadata.sync import sync_metadata
    from ...utils.config import read_api_key_from_yaml

    try:
        # Load API key
        api_key = read_api_key_from_yaml("youtube", "youtube.key")

        # Hardcoded channel ID for Einundzwanzig Podcast
        channel_id = "UCxSRxq14XIoMbFDEjMOPU5Q"

        # Sync metadata for the specific video
        result = sync_metadata(
            api_key=api_key,
            channel_id=channel_id,
            channel_title=channel_title,
            output_dir="./repository",
            max_videos=1,
            delay=0,
            force_refresh=request.force_refresh,
            specific_video_id=video_id,
        )

        if result["successful"] > 0:
            return {
                "success": True,
                "message": f"Successfully synced metadata for video: {video_id}",
            }
        else:
            raise HTTPException(
                status_code=500, detail=f"Failed to sync metadata for video: {video_id}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing metadata: {str(e)}")


@router.post("/{video_id}/platforms/youtube/download", response_model=DownloadResponse)
def download_youtube_video(
    video_id: str,
    request: DownloadRequest,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Download a video from YouTube
    """
    # Generate a simple user identifier (in a real app, this would be a session ID or user ID)
    user_id = f"user-{datetime.now().timestamp()}"

    result = video_service.download_video(
        video_id, channel_title, request.quality, user_id
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "message": f"Video {video_id} downloaded successfully from YouTube",
    }


@router.post("/{video_id}/platforms/nostrmedia/upload", response_model=DownloadResponse)
def upload_to_nostrmedia(
    video_id: str,
    request: NostrmediaUploadRequest,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service),
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
    if "youtube" not in video.platforms or not video.platforms["youtube"].downloaded:
        raise HTTPException(
            status_code=400,
            detail=f"Video {video_id} has not been downloaded from YouTube yet. Download it first.",
        )

    # Upload to nostrmedia
    result = video_service.upload_to_nostrmedia(
        video_id, channel_title, request.private_key, request.debug
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "message": f"Video {video_id} uploaded successfully to nostrmedia.com",
    }


@router.post("/{video_id}/platforms/nostrmedia", response_model=DownloadResponse)
def set_nostrmedia_url(
    video_id: str,
    request: NostrmediaUrlRequest,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service),
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
        request.uploaded_at or datetime.now().isoformat(),
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "message": f"Nostrmedia URL set successfully for video {video_id}",
    }


@router.post(
    "/{video_id}/platforms/youtube", response_model=DownloadResponse, tags=["platforms"]
)
def create_youtube_platform(
    video_id: str,
    request: YouTubePlatformRequest,
    channel_title: str = Depends(get_channel_title),
    video_service: VideoService = Depends(get_video_service),
):
    """
    Create YouTube platform data for a video from provided JSON data

    This endpoint accepts a JSON payload with the same structure as what the GET endpoint produces
    and creates the YouTube folder and files based on this data.

    - **video_id**: The YouTube video ID
    - **request**: JSON payload containing YouTube platform data

    The folder must not already exist with content, otherwise an error is returned.

    If the video doesn't exist in the database, it will be created with minimal metadata.

    Returns a success message if the platform data was successfully created.
    """
    # First, check if the video exists
    video_result = video_service.get_video(video_id, channel_title)

    # Extract title and other metadata from the request if available
    title = None
    published_at = None
    duration = 0

    if request.data and request.data.metadata:
        metadata_dict = request.data.metadata
        title = metadata_dict.get("title", f"YouTube video {video_id}")
        published_at = metadata_dict.get("published_at")
        duration = metadata_dict.get("duration", 0)
    else:
        title = f"YouTube video {video_id}"
        published_at = datetime.now().isoformat()

    if not video_result.success or not video_result.data:
        # If there's an error getting the video or it doesn't exist, create a minimal entry
        create_result = video_service.create_or_update_metadata(
            video_id=video_id,
            channel_title=channel_title,
            title=title,
            published_at=published_at,
            duration=duration,
        )

        if not create_result.success:
            raise HTTPException(status_code=500, detail=create_result.error)

        # Now get the newly created video
        video_result = video_service.get_video(video_id, channel_title)
        if not video_result.success:
            raise HTTPException(status_code=500, detail=video_result.error)

    video = video_result.data
    if not video:
        raise HTTPException(
            status_code=500, detail=f"Failed to create or retrieve video {video_id}"
        )

    # Check if the video already has YouTube platform data
    if "youtube" in video.platforms and video.platforms["youtube"].downloaded:
        raise HTTPException(
            status_code=409,  # Conflict
            detail=f"Video {video_id} already has YouTube platform data. Use PATCH to update.",
        )

    # Get the paths
    videos_dir = os.path.join(
        video_service.video_repository.base_dir, channel_title, "videos"
    )
    video_dir = get_video_dir(videos_dir, video_id)
    youtube_dir = get_platform_dir(video_dir, "youtube")

    # Check if the YouTube directory already exists
    if os.path.exists(youtube_dir):
        # Check if it has content
        dir_contents = os.listdir(youtube_dir)
        if dir_contents:  # If directory has content, it's a real conflict
            raise HTTPException(
                status_code=409,  # Conflict
                detail=f"YouTube directory for video {video_id} already exists and has content.",
            )
        # Otherwise, it's an empty directory that might have been created by a previous attempt
        # We'll continue and use it
    else:
        # Create the YouTube directory if it doesn't exist
        os.makedirs(youtube_dir, exist_ok=True)

    # Process the data and create files
    platform_data = request.data
    errors = []

    # Save metadata.json
    if platform_data.metadata:
        metadata_file = os.path.join(youtube_dir, "metadata.json")
        if not save_json_file(metadata_file, platform_data.metadata):
            errors.append("Failed to save metadata.json")

    # Save info.json
    if platform_data.info:
        info_file = os.path.join(youtube_dir, f"{video_id}.info.json")
        if not save_json_file(info_file, platform_data.info):
            errors.append("Failed to save info.json")

    # Save info_files if provided
    if platform_data.info_files:
        for filename, content in platform_data.info_files.items():
            file_path = os.path.join(youtube_dir, filename)
            if not save_json_file(file_path, content):
                errors.append(f"Failed to save {filename}")

    # Save description
    if platform_data.description:
        desc_file = os.path.join(youtube_dir, f"{video_id}.description")
        if not save_text_file(desc_file, platform_data.description):
            errors.append("Failed to save description file")

    # Save description_files if provided
    if platform_data.description_files:
        for filename, content in platform_data.description_files.items():
            file_path = os.path.join(youtube_dir, filename)
            if not save_text_file(file_path, content):
                errors.append(f"Failed to save {filename}")

    # Save live_chat
    if platform_data.live_chat:
        chat_file = os.path.join(youtube_dir, f"{video_id}.live_chat.json")
        if not save_json_file(chat_file, platform_data.live_chat):
            errors.append("Failed to save live_chat.json")

    # Save live_chat_files if provided
    if platform_data.live_chat_files:
        for filename, content in platform_data.live_chat_files.items():
            file_path = os.path.join(youtube_dir, filename)
            if not save_json_file(file_path, content):
                errors.append(f"Failed to save {filename}")

    # Save subtitles if provided
    if platform_data.subtitles:
        for filename, content in platform_data.subtitles.items():
            file_path = os.path.join(youtube_dir, filename)
            if not save_text_file(file_path, content):
                errors.append(f"Failed to save {filename}")

    # Update the video's platform data
    result = video_service.set_platform_data(
        video_id=video_id,
        channel_title=channel_title,
        platform_name="youtube",
        platform_url=request.url,
        downloaded=request.downloaded,
        downloaded_at=request.downloaded_at or datetime.now().isoformat(),
    )

    if not result.success:
        # If we failed to update the platform data, clean up the directory
        import shutil

        shutil.rmtree(youtube_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=result.error)

    # Return success with warnings if there were any errors
    if errors:
        return {
            "success": True,
            "message": f"YouTube platform data created for video {video_id} with warnings: {', '.join(errors)}",
        }

    return {
        "success": True,
        "message": f"YouTube platform data created successfully for video {video_id}",
    }

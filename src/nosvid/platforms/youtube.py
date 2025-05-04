"""
YouTube platform functionality for nosvid
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.filesystem import get_platform_dir, load_json_file, save_json_file


def get_youtube_metadata(video_dir: str) -> Dict[str, Any]:
    """
    Get YouTube metadata for a video

    Args:
        video_dir: Directory containing the video

    Returns:
        YouTube metadata dictionary
    """
    # Get the YouTube platform directory
    youtube_dir = get_platform_dir(video_dir, "youtube")

    # Load YouTube-specific metadata
    youtube_metadata_file = os.path.join(youtube_dir, "metadata.json")
    if os.path.exists(youtube_metadata_file):
        return load_json_file(youtube_metadata_file)

    return {}


def update_youtube_metadata(video_dir: str, metadata: Dict[str, Any]) -> None:
    """
    Update YouTube metadata for a video

    Args:
        video_dir: Directory containing the video
        metadata: YouTube metadata dictionary
    """
    # Get the YouTube platform directory
    youtube_dir = get_platform_dir(video_dir, "youtube")

    # Save YouTube-specific metadata
    youtube_metadata_file = os.path.join(youtube_dir, "metadata.json")
    save_json_file(youtube_metadata_file, metadata)


def find_youtube_video_file(video_dir: str) -> Optional[str]:
    """
    Find the YouTube video file for a video

    Args:
        video_dir: Directory containing the video

    Returns:
        Path to the video file, or None if not found
    """
    # Get the YouTube platform directory
    youtube_dir = get_platform_dir(video_dir, "youtube")

    # Find the video file
    video_files = []
    for file in os.listdir(youtube_dir):
        if file.endswith(".mp4") or file.endswith(".webm") or file.endswith(".mkv"):
            video_files.append(os.path.join(youtube_dir, file))

    if video_files:
        return video_files[0]

    return None

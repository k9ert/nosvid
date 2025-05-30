"""
YouTube platform functionality for nosvid
"""

import logging
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.config import load_config
from ..utils.filesystem import get_platform_dir, load_json_file, save_json_file

# Set up logging
logger = logging.getLogger(__name__)


def is_platform_activated() -> bool:
    """
    Check if the YouTube platform is activated in the config

    Returns:
        True if the platform is activated, False otherwise
    """
    config = load_config()
    return config.get("youtube", {}).get("activated", False)


def check_platform_activated() -> None:
    """
    Check if the YouTube platform is activated and raise an exception if not

    Raises:
        ValueError: If the platform is not activated
    """
    if not is_platform_activated():
        error_msg = (
            "YouTube platform is not activated. "
            "Please activate it in your config.yaml file by setting youtube.activated = true"
        )
        logger.error(f"Platform activation check failed: {error_msg}")
        logger.error(f"Stack trace: {traceback.format_stack()}")
        raise ValueError(error_msg)


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

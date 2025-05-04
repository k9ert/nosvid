"""
Common metadata operations for nosvid
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional

from ..utils.filesystem import load_json_file, save_json_file


def get_main_metadata(video_dir: str) -> Dict[str, Any]:
    """
    Get the main metadata for a video

    Args:
        video_dir: Directory containing the video

    Returns:
        Main metadata dictionary
    """
    # Load main metadata
    metadata_file = os.path.join(video_dir, "metadata.json")
    if os.path.exists(metadata_file):
        return load_json_file(metadata_file)

    return {}


def update_main_metadata(video_dir: str, metadata: Dict[str, Any]) -> None:
    """
    Update the main metadata for a video

    Args:
        video_dir: Directory containing the video
        metadata: Main metadata dictionary
    """
    # Save main metadata
    metadata_file = os.path.join(video_dir, "metadata.json")
    save_json_file(metadata_file, metadata)


def update_platform_metadata(
    main_metadata: Dict[str, Any], platform: str, platform_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update platform-specific metadata in the main metadata

    Args:
        main_metadata: Main metadata dictionary
        platform: Platform name (e.g., 'youtube', 'nostrmedia', 'nostr')
        platform_metadata: Platform-specific metadata dictionary

    Returns:
        Updated main metadata dictionary
    """
    # Initialize platforms dict if it doesn't exist
    if "platforms" not in main_metadata:
        main_metadata["platforms"] = {}

    # Update platform-specific metadata
    main_metadata["platforms"][platform] = platform_metadata

    return main_metadata


def get_platform_metadata(
    main_metadata: Dict[str, Any], platform: str
) -> Dict[str, Any]:
    """
    Get platform-specific metadata from the main metadata

    Args:
        main_metadata: Main metadata dictionary
        platform: Platform name (e.g., 'youtube', 'nostrmedia', 'nostr')

    Returns:
        Platform-specific metadata dictionary
    """
    # Check if platforms dict exists
    if "platforms" not in main_metadata:
        return {}

    # Check if platform-specific metadata exists
    if platform not in main_metadata["platforms"]:
        return {}

    return main_metadata["platforms"][platform]

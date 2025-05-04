"""
Nostrmedia platform functionality for nosvid
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional

from ..nostrmedia.upload import upload_to_nostrmedia
from ..utils.config import load_config
from ..utils.filesystem import get_platform_dir, load_json_file, save_json_file


def is_platform_activated() -> bool:
    """
    Check if the Nostrmedia platform is activated in the config

    Returns:
        True if the platform is activated, False otherwise
    """
    config = load_config()
    return config.get("nostrmedia", {}).get("activated", False)


def check_platform_activated() -> None:
    """
    Check if the Nostrmedia platform is activated and raise an exception if not

    Raises:
        ValueError: If the platform is not activated
    """
    if not is_platform_activated():
        raise ValueError(
            "Nostrmedia platform is not activated. "
            "Please activate it in your config.yaml file by setting nostrmedia.activated = true"
        )


def get_nostrmedia_metadata(video_dir: str) -> Dict[str, Any]:
    """
    Get Nostrmedia metadata for a video

    Args:
        video_dir: Directory containing the video

    Returns:
        Nostrmedia metadata dictionary
    """
    # Get the Nostrmedia platform directory
    nostrmedia_dir = get_platform_dir(video_dir, "nostrmedia")

    # Load Nostrmedia-specific metadata
    nostrmedia_metadata_file = os.path.join(nostrmedia_dir, "metadata.json")
    if os.path.exists(nostrmedia_metadata_file):
        return load_json_file(nostrmedia_metadata_file)

    return {}


def update_nostrmedia_metadata(video_dir: str, metadata: Dict[str, Any]) -> None:
    """
    Update Nostrmedia metadata for a video

    Args:
        video_dir: Directory containing the video
        metadata: Nostrmedia metadata dictionary
    """
    # Get the Nostrmedia platform directory
    nostrmedia_dir = get_platform_dir(video_dir, "nostrmedia")

    # Save Nostrmedia-specific metadata
    nostrmedia_metadata_file = os.path.join(nostrmedia_dir, "metadata.json")
    save_json_file(nostrmedia_metadata_file, metadata)


def upload_video_to_nostrmedia(
    video_file: str, private_key: Optional[str] = None, debug: bool = False
) -> Dict[str, Any]:
    """
    Upload a video to Nostrmedia

    Args:
        video_file: Path to the video file
        private_key: Private key string (hex or nsec format)
        debug: Whether to print debug information

    Returns:
        Dictionary with upload result
    """
    # Check if Nostrmedia platform is activated
    check_platform_activated()

    # Log that we're making a Nostrmedia API call
    print(f"Making Nostrmedia API call to upload video {video_file}")

    # Upload the video to Nostrmedia
    result = upload_to_nostrmedia(video_file, private_key, debug=debug)

    # Add timestamp to the result
    if "uploaded_at" not in result:
        result["uploaded_at"] = datetime.now().isoformat()

    return result

"""
Nostrmedia platform functionality for nosvid
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.filesystem import get_platform_dir, load_json_file, save_json_file
from ..nostrmedia.upload import upload_to_nostrmedia


def get_nostrmedia_metadata(video_dir: str) -> Dict[str, Any]:
    """
    Get Nostrmedia metadata for a video

    Args:
        video_dir: Directory containing the video

    Returns:
        Nostrmedia metadata dictionary
    """
    # Get the Nostrmedia platform directory
    nostrmedia_dir = get_platform_dir(video_dir, 'nostrmedia')

    # Load Nostrmedia-specific metadata
    nostrmedia_metadata_file = os.path.join(nostrmedia_dir, 'metadata.json')
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
    nostrmedia_dir = get_platform_dir(video_dir, 'nostrmedia')

    # Save Nostrmedia-specific metadata
    nostrmedia_metadata_file = os.path.join(nostrmedia_dir, 'metadata.json')
    save_json_file(nostrmedia_metadata_file, metadata)


def upload_video_to_nostrmedia(video_file: str, private_key: Optional[str] = None, debug: bool = False) -> Dict[str, Any]:
    """
    Upload a video to Nostrmedia

    Args:
        video_file: Path to the video file
        private_key: Private key string (hex or nsec format)
        debug: Whether to print debug information

    Returns:
        Dictionary with upload result
    """
    # Upload the video to Nostrmedia
    result = upload_to_nostrmedia(video_file, private_key, debug=debug)
    
    # Add timestamp to the result
    if 'uploaded_at' not in result:
        result['uploaded_at'] = datetime.now().isoformat()
    
    return result

"""
Filesystem utilities for nosvid
"""

import os
import json

def setup_directory_structure(base_dir, channel_title):
    """
    Set up the directory structure for downloads

    Args:
        base_dir: Base directory for downloads
        channel_title: Title of the channel

    Returns:
        Dictionary with paths to different directories
    """
    # Create main directory with channel name
    channel_dir = os.path.join(base_dir, channel_title.replace(' ', '_'))
    os.makedirs(channel_dir, exist_ok=True)

    # Create subdirectories
    videos_dir = os.path.join(channel_dir, 'videos')
    metadata_dir = os.path.join(channel_dir, 'metadata')

    os.makedirs(videos_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)

    return {
        'channel_dir': channel_dir,
        'videos_dir': videos_dir,
        'metadata_dir': metadata_dir
    }

def load_json_file(file_path, default=None):
    """
    Load JSON from file

    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid

    Returns:
        Parsed JSON data or default value
    """
    if default is None:
        default = {}

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default

    return default

def save_json_file(file_path, data):
    """
    Save data to JSON file

    Args:
        file_path: Path to JSON file
        data: Data to save
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_video_dir(videos_dir, video_id):
    """
    Get the directory for a specific video

    Args:
        videos_dir: Directory containing all videos
        video_id: ID of the video

    Returns:
        Path to the video directory
    """
    return os.path.join(videos_dir, video_id)

def get_platform_dir(video_dir, platform):
    """
    Get the directory for a specific platform within a video directory

    Args:
        video_dir: Directory for a specific video
        platform: Platform name (e.g., 'youtube', 'nostrmedia')

    Returns:
        Path to the platform directory
    """
    platform_dir = os.path.join(video_dir, platform)
    os.makedirs(platform_dir, exist_ok=True)
    return platform_dir

def create_safe_filename(title):
    """
    Create a safe filename from a title

    Args:
        title: Original title

    Returns:
        Safe filename
    """
    return "".join([c if c.isalnum() or c in ' ._-' else '_' for c in title])

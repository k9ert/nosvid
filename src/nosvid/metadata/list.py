"""
Listing functionality for nosvid
"""

import os
import json
import glob
from datetime import datetime
from ..utils.filesystem import load_json_file, save_json_file, get_video_dir

def generate_metadata_from_files(video_dir, video_id):
    """
    Generate metadata.json from existing files in the video directory

    Args:
        video_dir: Directory containing the video files
        video_id: ID of the video

    Returns:
        Dictionary with metadata
    """
    # Default metadata
    metadata = {
        'title': f"Video {video_id}",
        'video_id': video_id,
        'url': f"https://www.youtube.com/watch?v={video_id}",
        'published_at': '',
        'synced_at': datetime.now().isoformat(),
        'downloaded': False
    }

    # Try to get title and other info from info.json
    info_files = glob.glob(os.path.join(video_dir, "*.info.json"))
    if info_files:
        try:
            with open(info_files[0], 'r', encoding='utf-8') as f:
                info = json.load(f)
                if 'title' in info:
                    metadata['title'] = info['title']
                if 'upload_date' in info:
                    # Convert YYYYMMDD to ISO format
                    upload_date = info['upload_date']
                    if len(upload_date) == 8:
                        metadata['published_at'] = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}T00:00:00Z"
        except (json.JSONDecodeError, IOError):
            pass

    # Check if video is downloaded
    video_files = glob.glob(os.path.join(video_dir, "*.mp4")) + \
                 glob.glob(os.path.join(video_dir, "*.webm")) + \
                 glob.glob(os.path.join(video_dir, "*.mkv"))
    metadata['downloaded'] = len(video_files) > 0

    # Save the metadata file
    metadata_file = os.path.join(video_dir, 'metadata.json')
    save_json_file(metadata_file, metadata)

    return metadata

def list_videos(videos_dir, show_downloaded=True, show_not_downloaded=True):
    """
    List all videos in the repository

    Args:
        videos_dir: Directory containing videos
        show_downloaded: Whether to show downloaded videos
        show_not_downloaded: Whether to show videos that have not been downloaded

    Returns:
        List of video dictionaries
    """
    if not os.path.exists(videos_dir):
        print(f"Videos directory not found: {videos_dir}")
        return []

    videos = []

    for video_id in os.listdir(videos_dir):
        video_dir = get_video_dir(videos_dir, video_id)

        if not os.path.isdir(video_dir):
            continue

        metadata_file = os.path.join(video_dir, 'metadata.json')

        # If metadata.json doesn't exist, try to generate it from existing files
        if not os.path.exists(metadata_file):
            print(f"Generating metadata for video: {video_id}")
            metadata = generate_metadata_from_files(video_dir, video_id)
        else:
            metadata = load_json_file(metadata_file)

        # Filter based on download status
        if metadata.get('downloaded') and not show_downloaded:
            continue

        if not metadata.get('downloaded') and not show_not_downloaded:
            continue

        videos.append({
            'video_id': video_id,
            'title': metadata.get('title', 'Unknown'),
            'published_at': metadata.get('published_at', ''),
            'downloaded': metadata.get('downloaded', False),
            'url': metadata.get('url', '')
        })

    # Sort by published date (newest first)
    videos.sort(key=lambda x: x.get('published_at', ''), reverse=True)

    return videos

def print_video_list(videos, show_index=True):
    """
    Print a list of videos

    Args:
        videos: List of video dictionaries
        show_index: Whether to show the index number
    """
    if not videos:
        print("No videos found.")
        return

    print(f"\nFound {len(videos)} videos:")
    print("-" * 80)

    for i, video in enumerate(videos, 1):
        status = "✓" if video['downloaded'] else " "

        if show_index:
            print(f"{i:3d}. [{status}] {video['video_id']} - {video['title']} ({video['published_at']})")
        else:
            print(f"[{status}] {video['video_id']} - {video['title']} ({video['published_at']})")

    print("-" * 80)

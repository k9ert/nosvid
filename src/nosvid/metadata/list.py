"""
Listing functionality for nosvid
"""

import os
import json
import glob
from datetime import datetime
from ..utils.filesystem import load_json_file, save_json_file, get_video_dir, get_platform_dir

def generate_metadata_from_files(video_dir, video_id):
    """
    Generate metadata.json from existing files in the video directory

    Args:
        video_dir: Directory containing the video files
        video_id: ID of the video

    Returns:
        Dictionary with metadata
    """
    # Create platform-specific directory for YouTube
    youtube_dir = get_platform_dir(video_dir, 'youtube')

    # Default YouTube metadata
    youtube_metadata = {
        'title': f"Video {video_id}",
        'video_id': video_id,
        'url': f"https://www.youtube.com/watch?v={video_id}",
        'published_at': '',
        'synced_at': datetime.now().isoformat(),
        'downloaded': False
    }

    # Try to get title and other info from info.json
    info_files = glob.glob(os.path.join(youtube_dir, "*.info.json"))
    if info_files:
        try:
            with open(info_files[0], 'r', encoding='utf-8') as f:
                info = json.load(f)
                if 'title' in info:
                    youtube_metadata['title'] = info['title']
                if 'upload_date' in info:
                    # Convert YYYYMMDD to ISO format
                    upload_date = info['upload_date']
                    if len(upload_date) == 8:
                        youtube_metadata['published_at'] = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}T00:00:00Z"
        except (json.JSONDecodeError, IOError):
            pass

    # Check if video is downloaded
    video_files = glob.glob(os.path.join(youtube_dir, "*.mp4")) + \
                 glob.glob(os.path.join(youtube_dir, "*.webm")) + \
                 glob.glob(os.path.join(youtube_dir, "*.mkv"))
    youtube_metadata['downloaded'] = len(video_files) > 0

    # Save the YouTube metadata file
    youtube_metadata_file = os.path.join(youtube_dir, 'metadata.json')
    save_json_file(youtube_metadata_file, youtube_metadata)

    # Create main metadata with references to all platforms
    main_metadata = {
        'title': youtube_metadata['title'],
        'video_id': video_id,
        'published_at': youtube_metadata['published_at'],
        'synced_at': datetime.now().isoformat(),
        'platforms': {
            'youtube': {
                'url': youtube_metadata['url'],
                'downloaded': youtube_metadata['downloaded']
            }
        }
    }

    # Check for nostrmedia platform
    nostrmedia_dir = os.path.join(video_dir, 'nostrmedia')
    if os.path.exists(nostrmedia_dir):
        nostrmedia_metadata_file = os.path.join(nostrmedia_dir, 'metadata.json')
        if os.path.exists(nostrmedia_metadata_file):
            nostrmedia_metadata = load_json_file(nostrmedia_metadata_file)
            main_metadata['platforms']['nostrmedia'] = {
                'url': nostrmedia_metadata.get('url', ''),
                'hash': nostrmedia_metadata.get('hash', ''),
                'uploaded_at': nostrmedia_metadata.get('uploaded_at', '')
            }

    # Save the main metadata file
    main_metadata_file = os.path.join(video_dir, 'metadata.json')
    save_json_file(main_metadata_file, main_metadata)

    return main_metadata

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

        main_metadata_file = os.path.join(video_dir, 'metadata.json')

        # If metadata.json doesn't exist, try to generate it from existing files
        if not os.path.exists(main_metadata_file):
            print(f"Generating metadata for video: {video_id}")
            main_metadata = generate_metadata_from_files(video_dir, video_id)
        else:
            main_metadata = load_json_file(main_metadata_file)

        # Check if YouTube platform exists and get download status
        youtube_downloaded = False
        if 'platforms' in main_metadata and 'youtube' in main_metadata['platforms']:
            youtube_downloaded = main_metadata['platforms']['youtube'].get('downloaded', False)

        # Filter based on download status
        if youtube_downloaded and not show_downloaded:
            continue

        if not youtube_downloaded and not show_not_downloaded:
            continue

        # Check if nostrmedia platform exists
        has_nostrmedia = 'platforms' in main_metadata and 'nostrmedia' in main_metadata['platforms']
        nostrmedia_url = ''
        if has_nostrmedia:
            nostrmedia_url = main_metadata['platforms']['nostrmedia'].get('url', '')

        videos.append({
            'video_id': video_id,
            'title': main_metadata.get('title', 'Unknown'),
            'published_at': main_metadata.get('published_at', ''),
            'downloaded': youtube_downloaded,
            'url': main_metadata.get('platforms', {}).get('youtube', {}).get('url', ''),
            'nostrmedia_url': nostrmedia_url
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
    print("-" * 100)

    for i, video in enumerate(videos, 1):
        yt_status = "✓" if video['downloaded'] else " "
        nm_status = "✓" if video.get('nostrmedia_url') else " "

        published = video.get('published_at', '')[:10] if video.get('published_at') else 'Unknown'

        if show_index:
            print(f"{i:3d}. [YT:{yt_status}|NM:{nm_status}] {video['video_id']} - {video['title']} ({published})")
        else:
            print(f"[YT:{yt_status}|NM:{nm_status}] {video['video_id']} - {video['title']} ({published})")

    print("-" * 100)

"""
Metadata synchronization for nosvid
"""

import os
import subprocess
import time
import json
import glob
from datetime import datetime

from ..utils.filesystem import (
    setup_directory_structure,
    load_json_file,
    save_json_file,
    get_video_dir,
    get_platform_dir,
    create_safe_filename
)
from ..utils.youtube_api import get_channel_info, get_all_videos_from_channel

def load_sync_history(metadata_dir):
    """
    Load the history of synced videos

    Args:
        metadata_dir: Directory containing metadata

    Returns:
        Dictionary with sync history
    """
    history_file = os.path.join(metadata_dir, 'sync_history.json')
    return load_json_file(history_file)

def save_sync_history(metadata_dir, history):
    """
    Save the updated sync history

    Args:
        metadata_dir: Directory containing metadata
        history: Sync history data
    """
    history_file = os.path.join(metadata_dir, 'sync_history.json')
    save_json_file(history_file, history)

def fetch_video_metadata(video, videos_dir):
    """
    Fetch metadata for a video using yt-dlp without downloading the video

    Args:
        video: Video dictionary
        videos_dir: Directory containing videos

    Returns:
        Dictionary with result information
    """
    video_id = video['video_id']
    video_url = video['url']
    title = video['title']

    # Create a directory for this video using the video ID inside the videos directory
    video_dir = get_video_dir(videos_dir, video_id)
    os.makedirs(video_dir, exist_ok=True)

    # Create platform-specific directory for YouTube
    youtube_dir = get_platform_dir(video_dir, 'youtube')

    # Create a safe filename from the title
    safe_title = create_safe_filename(title)
    output_template = os.path.join(youtube_dir, f"{safe_title}")

    print(f"Fetching metadata for: {title} ({video_id})")

    # Prepare yt-dlp command to fetch only metadata
    cmd = [
        'yt-dlp',
        '--skip-download',
        '--write-info-json',
        '--write-thumbnail',
        '--write-description',
        '--write-subs',
        '--sub-langs', 'all',
        '--no-overwrites',
        '-o', output_template,
        video_url
    ]

    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Successfully fetched metadata for: {title}")

            # Try to extract duration from info.json file
            duration = 0
            info_files = glob.glob(os.path.join(youtube_dir, "*.info.json"))
            if info_files:
                try:
                    with open(info_files[0], 'r', encoding='utf-8') as f:
                        info_data = json.load(f)
                        if 'duration' in info_data:
                            duration = info_data['duration']
                except Exception as e:
                    print(f"Error reading info file for duration: {e}")

            # Create a YouTube-specific metadata.json file
            youtube_metadata = {
                'title': title,
                'video_id': video_id,
                'url': video_url,
                'published_at': video['published_at'],
                'synced_at': datetime.now().isoformat(),
                'downloaded': False,
                'duration': duration
            }

            # Save YouTube-specific metadata
            youtube_metadata_file = os.path.join(youtube_dir, 'metadata.json')
            save_json_file(youtube_metadata_file, youtube_metadata)

            # Create main metadata.json file with references to all platforms
            main_metadata = {
                'title': title,
                'video_id': video_id,
                'published_at': video['published_at'],
                'duration': duration,  # Add duration field
                'synced_at': datetime.now().isoformat(),
                'platforms': {
                    'youtube': {
                        'url': video_url,
                        'downloaded': False
                    }
                }
            }

            # Save main metadata
            main_metadata_file = os.path.join(video_dir, 'metadata.json')
            save_json_file(main_metadata_file, main_metadata)

            return {
                'success': True,
                'metadata_dir': video_dir,
                'timestamp': datetime.now().isoformat(),
                'error': None
            }
        else:
            print(f"Error fetching metadata for {title}: {result.stderr}")
            return {
                'success': False,
                'metadata_dir': None,
                'timestamp': datetime.now().isoformat(),
                'error': result.stderr
            }
    except Exception as e:
        print(f"Exception while fetching metadata for {title}: {str(e)}")
        return {
            'success': False,
            'metadata_dir': None,
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }

def sync_metadata(api_key, channel_id, channel_title, output_dir, max_videos=None, delay=5, force_refresh=False):
    """
    Sync metadata for all videos in a channel

    Args:
        api_key: YouTube API key
        channel_id: ID of the channel
        channel_title: Title of the channel
        output_dir: Base directory for downloads
        max_videos: Maximum number of videos to sync (None for all)
        delay: Delay between operations in seconds
        force_refresh: Force refresh from API even if cache is fresh

    Returns:
        Dictionary with sync results
    """
    # Get channel info for saving metadata
    channel_info = {
        'title': channel_title,
        'description': '',
        'published_at': '',
        'thumbnail_url': ''
    }

    # Try to get more detailed info if possible
    try:
        detailed_info = get_channel_info(api_key, channel_id)
        if detailed_info['title'] != 'Unknown Channel':
            channel_info = detailed_info
    except Exception as e:
        print(f"Warning: Could not get detailed channel info: {e}")

    # Set up directory structure
    dirs = setup_directory_structure(output_dir, channel_title)

    # Save channel info
    channel_info_file = os.path.join(dirs['metadata_dir'], 'channel_info.json')
    save_json_file(channel_info_file, channel_info)

    # Load sync history
    sync_history = load_sync_history(dirs['metadata_dir'])

    # Get videos from channel (using cache if available and not forced to refresh)
    print(f"Getting videos from channel ID: {channel_id}")
    videos = get_all_videos_from_channel(
        api_key=api_key,
        channel_id=channel_id,
        metadata_dir=dirs['metadata_dir'],
        force_refresh=force_refresh,
        max_pages=None
    )

    print(f"Found {len(videos)} videos")

    # Sort videos by published date (newest first)
    videos.sort(key=lambda x: x['published_at'], reverse=True)

    # Filter out videos that are already synced
    new_videos = []
    already_synced = 0

    for video in videos:
        video_id = video['video_id']
        if video_id in sync_history and sync_history[video_id].get('success'):
            already_synced += 1
        else:
            new_videos.append(video)

    print(f"Found {len(new_videos)} new videos (already synced: {already_synced})")

    # Limit number of new videos if specified
    if max_videos and max_videos > 0:
        if len(new_videos) > max_videos:
            new_videos = new_videos[:max_videos]
            print(f"Limited to {len(new_videos)} new videos")

    # Fetch metadata for each video
    successful = 0
    failed = 0

    for i, video in enumerate(new_videos, 1):
        video_id = video['video_id']
        print(f"\nProcessing video {i}/{len(new_videos)}")

        # Fetch metadata
        result = fetch_video_metadata(video, dirs['videos_dir'])

        if result['success']:
            successful += 1
        else:
            failed += 1

        # Update sync history
        sync_history[video_id] = {
            'title': video['title'],
            'published_at': video['published_at'],
            'url': video['url'],
            'sync_attempts': sync_history.get(video_id, {}).get('sync_attempts', 0) + 1,
            'last_attempt': datetime.now().isoformat(),
            'success': result['success'],
            'metadata_dir': result['metadata_dir'],
            'error': result['error']
        }

        # Save sync history after each video
        save_sync_history(dirs['metadata_dir'], sync_history)

        # Add delay between operations
        if i < len(new_videos):
            print(f"Waiting {delay} seconds before next operation...")
            time.sleep(delay)

    print("\nMetadata sync completed!")
    print(f"Successfully synced: {successful}")
    print(f"Failed: {failed}")
    print(f"Already synced: {already_synced}")

    return {
        'total': len(videos),
        'new_videos': len(new_videos),
        'successful': successful,
        'failed': failed,
        'already_synced': already_synced,
        'channel_title': channel_title,
        'output_dir': output_dir
    }

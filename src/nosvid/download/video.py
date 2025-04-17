"""
Video download functionality for nosvid
"""

import os
import subprocess
from datetime import datetime

from ..utils.filesystem import (
    load_json_file,
    save_json_file,
    get_video_dir,
    get_platform_dir,
    create_safe_filename
)

def download_video(video_id, videos_dir, quality='best'):
    """
    Download a video using yt-dlp

    Args:
        video_id: ID of the video
        videos_dir: Directory containing videos
        quality: Video quality (e.g., best, 720p, etc.)

    Returns:
        Boolean indicating success
    """
    # Find the video directory
    video_dir = get_video_dir(videos_dir, video_id)

    if not os.path.exists(video_dir):
        print(f"Error: Video directory not found for ID {video_id}")
        return False

    # Load main metadata
    main_metadata_file = os.path.join(video_dir, 'metadata.json')

    if not os.path.exists(main_metadata_file):
        print(f"Error: Main metadata file not found for ID {video_id}")
        return False

    main_metadata = load_json_file(main_metadata_file)

    # Check if YouTube platform exists in metadata
    if 'platforms' not in main_metadata or 'youtube' not in main_metadata['platforms']:
        print(f"Error: YouTube platform not found in metadata for ID {video_id}")
        return False

    # Get YouTube platform data
    youtube_platform = main_metadata['platforms']['youtube']
    video_url = youtube_platform['url']
    title = main_metadata['title']

    # Create platform-specific directory for YouTube
    youtube_dir = get_platform_dir(video_dir, 'youtube')

    # Load YouTube-specific metadata
    youtube_metadata_file = os.path.join(youtube_dir, 'metadata.json')
    youtube_metadata = load_json_file(youtube_metadata_file, {
        'title': title,
        'video_id': video_id,
        'url': video_url,
        'downloaded': False
    })

    # Create a safe filename from the title
    safe_title = create_safe_filename(title)
    output_template = os.path.join(youtube_dir, f"{safe_title}.%(ext)s")

    print(f"Downloading video: {title} ({video_id})")

    # Prepare yt-dlp command
    cmd = [
        'yt-dlp',
        '--format', quality,
        '--embed-subs',
        '--embed-metadata',
        '--embed-thumbnail',
        '--no-overwrites',
        '--continue',
        '-o', output_template,
        video_url
    ]

    try:
        # Run the download command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Successfully downloaded: {title}")

            # Update YouTube-specific metadata to mark as downloaded
            youtube_metadata['downloaded'] = True
            youtube_metadata['downloaded_at'] = datetime.now().isoformat()
            save_json_file(youtube_metadata_file, youtube_metadata)

            # Update main metadata to mark YouTube as downloaded
            main_metadata['platforms']['youtube']['downloaded'] = True
            main_metadata['platforms']['youtube']['downloaded_at'] = datetime.now().isoformat()
            save_json_file(main_metadata_file, main_metadata)

            return True
        else:
            print(f"Error downloading {title}: {result.stderr}")
            return False
    except Exception as e:
        print(f"Exception while downloading {title}: {str(e)}")
        return False

def download_all_pending(videos_dir, quality='best', delay=5):
    """
    Download all videos that have not been downloaded yet

    Args:
        videos_dir: Directory containing videos
        quality: Video quality (e.g., best, 720p, etc.)
        delay: Delay between downloads in seconds

    Returns:
        Dictionary with download results
    """
    from ..metadata.list import list_videos
    import time

    videos, _ = list_videos(videos_dir, show_downloaded=False, show_not_downloaded=True)

    if not videos:
        print("No videos to download.")
        return {
            'total': 0,
            'successful': 0,
            'failed': 0
        }

    print(f"\nDownloading {len(videos)} videos...")

    successful = 0
    failed = 0

    for i, video in enumerate(videos, 1):
        video_id = video['video_id']
        print(f"\nDownloading video {i}/{len(videos)}: {video['title']}")

        success = download_video(video_id, videos_dir, quality=quality)

        if success:
            print(f"Successfully downloaded video: {video_id}")
            successful += 1
        else:
            print(f"Failed to download video: {video_id}")
            failed += 1

        # Add delay between downloads
        if i < len(videos):
            print(f"Waiting {delay} seconds before next download...")
            time.sleep(delay)

    print("\nAll downloads completed!")
    print(f"Successfully downloaded: {successful}")
    print(f"Failed: {failed}")

    return {
        'total': len(videos),
        'successful': successful,
        'failed': failed
    }

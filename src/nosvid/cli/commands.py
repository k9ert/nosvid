"""
Command-line interface commands for nosvid
"""

import argparse
import sys
import os
from datetime import datetime

from ..utils.config import read_api_key_from_yaml, get_default_output_dir
from ..utils.filesystem import setup_directory_structure, load_json_file, save_json_file
from ..utils.youtube_api import get_channel_info
from ..metadata.sync import sync_metadata
from ..metadata.list import list_videos, print_video_list
from ..download.video import download_video, download_all_pending
from ..nostrmedia.upload import upload_to_nostrmedia

def sync_command(args):
    """
    Sync metadata for all videos in a channel

    Args:
        args: Command-line arguments
    """
    try:
        # Load API key
        api_key = read_api_key_from_yaml('youtube', 'youtube.key')

        # Hardcoded channel ID for Einundzwanzig Podcast
        channel_id = "UCxSRxq14XIoMbFDEjMOPU5Q"
        print(f"Using channel ID: {channel_id}")

        # Get channel title, first from mapping, then from API if needed
        # We need to get the title here because sync_metadata needs it for the API call
        channel_title = get_channel_title(api_key, channel_id)
        print(f"Channel title: {channel_title}")

        # Sync metadata
        result = sync_metadata(
            api_key=api_key,
            channel_id=channel_id,
            channel_title=channel_title,
            output_dir=args.output_dir,
            max_videos=args.max_videos,
            delay=args.delay
        )

        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

# Dictionary mapping channel IDs to their titles
CHANNEL_MAPPING = {
    "UCxSRxq14XIoMbFDEjMOPU5Q": "Einundzwanzig"
}

def get_channel_title(api_key, channel_id):
    """
    Get channel title, first from mapping, then from API if not found

    Args:
        api_key: YouTube API key
        channel_id: ID of the channel

    Returns:
        Channel title
    """
    # First check if we have a hardcoded mapping
    if channel_id in CHANNEL_MAPPING:
        return CHANNEL_MAPPING[channel_id]

    # If not, call the API
    channel_info = get_channel_info(api_key, channel_id)
    return channel_info['title']

def list_command(args):
    """
    List videos in the repository

    Args:
        args: Command-line arguments
    """
    try:
        # Hardcoded channel ID for Einundzwanzig Podcast
        channel_id = "UCxSRxq14XIoMbFDEjMOPU5Q"

        # Get channel title from mapping (no API call)
        channel_title = CHANNEL_MAPPING[channel_id]
        print(f"Channel title: {channel_title}")

        # Set up directory structure
        dirs = setup_directory_structure(args.output_dir, channel_title)

        # Determine which videos to show
        show_downloaded = True
        show_not_downloaded = True

        if args.downloaded and not args.not_downloaded:
            show_not_downloaded = False

        if args.not_downloaded and not args.downloaded:
            show_downloaded = False

        # List videos
        videos = list_videos(
            videos_dir=dirs['videos_dir'],
            show_downloaded=show_downloaded,
            show_not_downloaded=show_not_downloaded
        )

        # Print the list
        print_video_list(videos)

        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def download_command(args):
    """
    Download videos

    Args:
        args: Command-line arguments
    """
    try:
        # Load API key
        api_key = read_api_key_from_yaml('youtube', 'youtube.key')

        # Hardcoded channel ID for Einundzwanzig Podcast
        channel_id = "UCxSRxq14XIoMbFDEjMOPU5Q"

        # Get channel title, first from mapping, then from API if needed
        channel_title = get_channel_title(api_key, channel_id)
        print(f"Channel title: {channel_title}")

        # Set up directory structure
        dirs = setup_directory_structure(args.output_dir, channel_title)

        # Download specific video or all pending videos
        if args.video_id:
            # Download specific video
            success = download_video(
                video_id=args.video_id,
                videos_dir=dirs['videos_dir'],
                quality=args.quality
            )

            if success:
                print(f"Successfully downloaded video: {args.video_id}")
                return 0
            else:
                print(f"Failed to download video: {args.video_id}")
                return 1
        else:
            # Download all pending videos
            result = download_all_pending(
                videos_dir=dirs['videos_dir'],
                quality=args.quality,
                delay=args.delay
            )

            if result['successful'] > 0:
                return 0
            elif result['total'] == 0:
                print("No videos to download.")
                return 0
            else:
                print("All downloads failed.")
                return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def nostrmedia_command(args):
    """
    Upload videos to nostrmedia.com

    Args:
        args: Command-line arguments
    """
    try:
        # Check if a video ID is provided
        if not args.video_id:
            print("Error: No video ID provided.")
            return 1

        # Load API key (for getting channel info)
        api_key = read_api_key_from_yaml('youtube', 'youtube.key')

        # Hardcoded channel ID for Einundzwanzig Podcast
        channel_id = "UCxSRxq14XIoMbFDEjMOPU5Q"

        # Get channel title, first from mapping, then from API if needed
        channel_title = get_channel_title(api_key, channel_id)
        print(f"Channel title: {channel_title}")

        # Set up directory structure
        dirs = setup_directory_structure(args.output_dir, channel_title)

        # Find the video directory
        video_dir = os.path.join(dirs['videos_dir'], args.video_id)

        if not os.path.exists(video_dir):
            print(f"Error: Video directory not found for ID {args.video_id}")
            return 1

        # Find video files in the directory
        video_files = []
        for ext in ['.mp4', '.webm', '.mkv']:
            video_files.extend([os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith(ext)])

        if not video_files:
            print(f"Error: No video files found in {video_dir}")
            return 1

        # Use the first video file found
        video_file = video_files[0]
        print(f"Found video file: {os.path.basename(video_file)}")

        # Upload the video to nostrmedia.com
        result = upload_to_nostrmedia(video_file, args.private_key)

        if result['success']:
            print(f"Video uploaded successfully to: {result['url']}")

            # Update metadata to include the nostrmedia URL
            metadata_file = os.path.join(video_dir, 'metadata.json')
            if os.path.exists(metadata_file):
                metadata = load_json_file(metadata_file)
                metadata['nostrmedia_url'] = result['url']
                metadata['nostrmedia_hash'] = result['hash']
                metadata['nostrmedia_uploaded_at'] = datetime.now().isoformat()
                save_json_file(metadata_file, metadata)
                print(f"Updated metadata with nostrmedia URL")

            return 0
        else:
            print(f"Error uploading video: {result['error']}")
            return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

        # Download specific video or all pending videos
        if args.video_id:
            # Download specific video
            success = download_video(
                video_id=args.video_id,
                videos_dir=dirs['videos_dir'],
                quality=args.quality
            )

            if success:
                print(f"Successfully downloaded video: {args.video_id}")
                return 0
            else:
                print(f"Failed to download video: {args.video_id}")
                return 1
        else:
            # Download all pending videos
            result = download_all_pending(
                videos_dir=dirs['videos_dir'],
                quality=args.quality,
                delay=args.delay
            )

            if result['successful'] > 0:
                return 0
            elif result['total'] == 0:
                print("No videos to download.")
                return 0
            else:
                print("All downloads failed.")
                return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def main():
    """
    Main entry point for the CLI
    """
    # Create the top-level parser
    parser = argparse.ArgumentParser(
        prog='nosvid',
        description='A tool for downloading and managing YouTube videos'
    )

    # Add global arguments
    parser.add_argument(
        '--output-dir',
        type=str,
        default=get_default_output_dir(),
        help='Base directory for downloads'
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        title='commands',
        dest='command',
        help='Command to execute'
    )

    # Create the parser for the "sync" command
    sync_parser = subparsers.add_parser(
        'sync',
        help='Sync metadata for all videos in a channel'
    )
    sync_parser.add_argument(
        '--max-videos',
        type=int,
        default=5,
        help='Maximum number of videos to sync (default: 5, use 0 for all)'
    )
    sync_parser.add_argument(
        '--delay',
        type=int,
        default=5,
        help='Delay between operations in seconds'
    )

    # Create the parser for the "list" command
    list_parser = subparsers.add_parser(
        'list',
        help='List videos in the repository'
    )
    list_parser.add_argument(
        '--downloaded',
        action='store_true',
        help='Show only downloaded videos'
    )
    list_parser.add_argument(
        '--not-downloaded',
        action='store_true',
        help='Show only videos that have not been downloaded'
    )

    # Create the parser for the "download" command
    download_parser = subparsers.add_parser(
        'download',
        help='Download videos'
    )
    download_parser.add_argument(
        'video_id',
        type=str,
        nargs='?',
        help='ID of the video to download (if not specified, download all pending videos)'
    )
    download_parser.add_argument(
        '--quality',
        type=str,
        default='best',
        help='Video quality (e.g., best, 720p, etc.)'
    )
    download_parser.add_argument(
        '--delay',
        type=int,
        default=5,
        help='Delay between downloads in seconds'
    )

    # Create the parser for the "nostrmedia" command
    nostrmedia_parser = subparsers.add_parser(
        'nostrmedia',
        help='Upload videos to nostrmedia.com'
    )
    nostrmedia_parser.add_argument(
        'video_id',
        type=str,
        help='ID of the video to upload'
    )
    nostrmedia_parser.add_argument(
        '--private-key',
        type=str,
        help='Private key string (hex or nsec format, if not provided, a new key will be generated)'
    )

    # Parse arguments
    args = parser.parse_args()

    # Execute the appropriate command
    if args.command == 'sync':
        return sync_command(args)
    elif args.command == 'list':
        return list_command(args)
    elif args.command == 'download':
        return download_command(args)
    elif args.command == 'nostrmedia':
        return nostrmedia_command(args)
    else:
        parser.print_help()
        return 0

if __name__ == '__main__':
    sys.exit(main())

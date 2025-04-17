"""
Sync command for nosvid CLI
"""

from .base import get_channel_title
from ...utils.config import get_default_download_delay
from ...utils.config import read_api_key_from_yaml
from ...metadata.sync import sync_metadata

def sync_command(args):
    """
    Sync metadata for all videos in a channel

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        # Load API key
        api_key = read_api_key_from_yaml('youtube', 'youtube.key')

        # Hardcoded channel ID for Einundzwanzig Podcast
        channel_id = "UCxSRxq14XIoMbFDEjMOPU5Q"

        channel_title = get_channel_title()
        print(f"Channel title: {channel_title}")

        # If a specific video ID is provided, sync only that video
        if args.video_id:
            print(f"Syncing metadata for video: {args.video_id}")
            # Sync metadata for a specific video
            result = sync_metadata(
                api_key=api_key,
                channel_id=channel_id,
                channel_title=channel_title,
                output_dir=args.output_dir,
                max_videos=1,
                delay=args.delay,
                force_refresh=args.force_refresh,
                specific_video_id=args.video_id
            )
            if result['successful'] > 0:
                print(f"Successfully synced metadata for video: {args.video_id}")
                return 0
            else:
                print(f"Failed to sync metadata for video: {args.video_id}")
                return 1

        # Otherwise, sync all videos in the channel
        print(f"Syncing metadata for all videos in channel: {channel_title}")

        # Sync channel videos
        result = sync_metadata(
            api_key=api_key,
            channel_id=channel_id,
            channel_title=channel_title,
            output_dir=args.output_dir,
            max_videos=args.max_videos,
            delay=args.delay,
            force_refresh=args.force_refresh
        )

        if result:
            print(f"Successfully synced metadata for channel: {channel_title}")
            return 0
        else:
            print(f"Failed to sync metadata for channel: {channel_title}")
            return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def register_sync_parser(subparsers):
    """
    Register the sync command parser

    Args:
        subparsers: Subparsers object from argparse
    """
    sync_parser = subparsers.add_parser(
        'sync',
        help='Sync metadata for all videos in a channel'
    )
    sync_parser.add_argument(
        'video_id',
        type=str,
        nargs='?',
        help='ID of the video to sync (if not specified, sync all videos)'
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
        default=get_default_download_delay(),
        help='Delay between operations in seconds'
    )
    sync_parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='Force refresh from YouTube API even if cache is fresh'
    )

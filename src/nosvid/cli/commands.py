"""
Command-line interface commands for nosvid
"""

import argparse
import sys
import os
from datetime import datetime

from ..utils.config import read_api_key_from_yaml, get_default_output_dir, get_default_video_quality, get_default_download_delay
from ..utils.filesystem import setup_directory_structure, load_json_file, save_json_file, get_platform_dir
from ..utils.youtube_api import get_channel_info
from ..metadata.sync import sync_metadata
from ..metadata.list import list_videos, print_video_list
from ..download.video import download_video, download_all_pending
from ..nostrmedia.upload import upload_to_nostrmedia
from ..nostr.upload import upload_to_nostr

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

        # Check if a specific video ID is provided
        if hasattr(args, 'video_id') and args.video_id:
            print(f"Syncing metadata for specific video: {args.video_id}")
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
        else:
            # Sync metadata for all videos
            result = sync_metadata(
                api_key=api_key,
                channel_id=channel_id,
                channel_title=channel_title,
                output_dir=args.output_dir,
                max_videos=args.max_videos,
                delay=args.delay,
                force_refresh=args.force_refresh
            )

        # Check the result
        if result['successful'] > 0:
            return 0
        elif result['total'] == 0:
            print("No videos to sync.")
            return 0
        else:
            print("All syncs failed.")
            return 1
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

        # List videos and get repository stats
        videos, stats = list_videos(
            videos_dir=dirs['videos_dir'],
            metadata_dir=dirs['metadata_dir'],
            channel_id=channel_id,
            show_downloaded=show_downloaded,
            show_not_downloaded=show_not_downloaded
        )

        # Print the list with repository status summary
        print_video_list(videos, stats)

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

        # Find video files in the youtube subdirectory
        youtube_dir = os.path.join(video_dir, 'youtube')
        if not os.path.exists(youtube_dir):
            print(f"YouTube directory not found for ID {args.video_id}")
            print("Automatically downloading the video first...")

            # Create a new args object with the same video_id
            download_args = type('Args', (), {'video_id': args.video_id, 'output_dir': args.output_dir, 'quality': 'best'})

            # Call download_command to download the video
            download_result = download_command(download_args)

            if download_result != 0:
                print(f"Error: Failed to download video {args.video_id}")
                return 1

            # Check again if the directory exists after download
            if not os.path.exists(youtube_dir):
                print(f"Error: YouTube directory still not found after download for ID {args.video_id}")
                return 1

        video_files = []
        for ext in ['.mp4', '.webm', '.mkv']:
            video_files.extend([os.path.join(youtube_dir, f) for f in os.listdir(youtube_dir) if f.endswith(ext)])

        if not video_files:
            print(f"No video files found in {youtube_dir}")
            print("Automatically downloading the video first...")

            # Create a new args object with the same video_id
            download_args = type('Args', (), {'video_id': args.video_id, 'output_dir': args.output_dir, 'quality': 'best'})

            # Call download_command to download the video
            download_result = download_command(download_args)

            if download_result != 0:
                print(f"Error: Failed to download video {args.video_id}")
                return 1

            # Check again for video files after download
            video_files = []
            for ext in ['.mp4', '.webm', '.mkv']:
                video_files.extend([os.path.join(youtube_dir, f) for f in os.listdir(youtube_dir) if f.endswith(ext)])

            if not video_files:
                print(f"Error: No video files found in {youtube_dir} even after download")
                return 1

        # Use the first video file found
        video_file = video_files[0]
        print(f"Found video file: {os.path.basename(video_file)}")

        # Upload the video to nostrmedia.com
        result = upload_to_nostrmedia(video_file, args.private_key, debug=args.debug)

        if result['success']:
            print(f"Video uploaded successfully to: {result['url']}")

            # Create platform-specific directory for nostrmedia
            nostrmedia_dir = get_platform_dir(video_dir, 'nostrmedia')

            # Create nostrmedia-specific metadata
            nostrmedia_metadata = {
                'url': result['url'],
                'hash': result['hash'],
                'uploaded_at': datetime.now().isoformat()
            }

            # Save nostrmedia-specific metadata
            nostrmedia_metadata_file = os.path.join(nostrmedia_dir, 'metadata.json')
            save_json_file(nostrmedia_metadata_file, nostrmedia_metadata)

            # Update main metadata to include the nostrmedia platform
            main_metadata_file = os.path.join(video_dir, 'metadata.json')
            if os.path.exists(main_metadata_file):
                main_metadata = load_json_file(main_metadata_file)

                # Initialize platforms dict if it doesn't exist
                if 'platforms' not in main_metadata:
                    main_metadata['platforms'] = {}

                # Add nostrmedia platform
                main_metadata['platforms']['nostrmedia'] = {
                    'url': result['url'],
                    'hash': result['hash'],
                    'uploaded_at': datetime.now().isoformat()
                }

                save_json_file(main_metadata_file, main_metadata)
                print(f"Updated metadata with nostrmedia URL")

            return 0
        else:
            print(f"Error uploading video: {result['error']}")
            return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def nostr_command(args):
    """
    Upload videos to the Nostr network

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

        # If video directory doesn't exist, sync metadata first
        if not os.path.exists(video_dir):
            print(f"Video directory not found for ID {args.video_id}")
            print("Automatically syncing metadata first...")

            # Create a new args object for sync
            sync_args = type('Args', (), {
                'output_dir': args.output_dir,
                'max_videos': 1,
                'delay': 0,
                'force_refresh': True,
                'video_id': args.video_id
            })

            # Call sync_command to get metadata
            sync_result = sync_command(sync_args)

            if sync_result != 0:
                print(f"Error: Failed to sync metadata for video {args.video_id}")
                return 1

            # Check again if the directory exists after sync
            if not os.path.exists(video_dir):
                print(f"Error: Video directory still not found after sync for ID {args.video_id}")
                return 1

        # Load the video metadata
        metadata_file = os.path.join(video_dir, 'metadata.json')
        if not os.path.exists(metadata_file):
            print(f"Metadata file not found for ID {args.video_id}")
            print("Automatically syncing metadata first...")

            # Create a new args object for sync
            sync_args = type('Args', (), {
                'output_dir': args.output_dir,
                'max_videos': 1,
                'delay': 0,
                'force_refresh': True,
                'video_id': args.video_id
            })

            # Call sync_command to get metadata
            sync_result = sync_command(sync_args)

            if sync_result != 0:
                print(f"Error: Failed to sync metadata for video {args.video_id}")
                return 1

            # Check again if the metadata file exists after sync
            if not os.path.exists(metadata_file):
                print(f"Error: Metadata file still not found after sync for ID {args.video_id}")
                return 1

        metadata = load_json_file(metadata_file)

        # Find video files in the youtube subdirectory
        youtube_dir = os.path.join(video_dir, 'youtube')
        if not os.path.exists(youtube_dir):
            print(f"YouTube directory not found for ID {args.video_id}")
            print("Automatically downloading the video first...")

            # Create a new args object with the same video_id
            download_args = type('Args', (), {'video_id': args.video_id, 'output_dir': args.output_dir, 'quality': 'best'})

            # Call download_command to download the video
            download_result = download_command(download_args)

            if download_result != 0:
                print(f"Error: Failed to download video {args.video_id}")
                return 1

            # Check again if the directory exists after download
            if not os.path.exists(youtube_dir):
                print(f"Error: YouTube directory still not found after download for ID {args.video_id}")
                return 1

        video_files = []
        for ext in ['.mp4', '.webm', '.mkv']:
            video_files.extend([os.path.join(youtube_dir, f) for f in os.listdir(youtube_dir) if f.endswith(ext)])

        if not video_files:
            print(f"No video files found in {youtube_dir}")
            print("Automatically downloading the video first...")

            # Create a new args object with the same video_id
            download_args = type('Args', (), {'video_id': args.video_id, 'output_dir': args.output_dir, 'quality': 'best'})

            # Call download_command to download the video
            download_result = download_command(download_args)

            if download_result != 0:
                print(f"Error: Failed to download video {args.video_id}")
                return 1

            # Check again for video files after download
            video_files = []
            for ext in ['.mp4', '.webm', '.mkv']:
                video_files.extend([os.path.join(youtube_dir, f) for f in os.listdir(youtube_dir) if f.endswith(ext)])

            if not video_files:
                print(f"Error: No video files found in {youtube_dir} even after download")
                return 1

        # Use the first video file found
        video_file = video_files[0]
        print(f"Found video file: {os.path.basename(video_file)}")

        # Add video_id to metadata
        metadata['video_id'] = args.video_id

        # Add YouTube URL to metadata if not present
        if 'youtube_url' not in metadata:
            metadata['youtube_url'] = f"https://www.youtube.com/watch?v={args.video_id}"

        # Check if the video has already been uploaded to nostrmedia
        if 'platforms' in metadata and 'nostrmedia' in metadata['platforms']:
            nostrmedia_data = metadata['platforms']['nostrmedia']
            if 'url' in nostrmedia_data:
                metadata['nostrmedia_url'] = nostrmedia_data['url']
                print(f"Found nostrmedia URL: {metadata['nostrmedia_url']}")

        # If not uploaded to nostrmedia yet, automatically upload it
        if 'nostrmedia_url' not in metadata:
            print("Note: This video has not been uploaded to nostrmedia yet.")
            print(f"Automatically uploading to nostrmedia first...")

            # Call nostrmedia_command with the same arguments
            nostrmedia_result = nostrmedia_command(args)

            if nostrmedia_result != 0:
                print("Failed to upload to nostrmedia. Continuing with YouTube URL for embedding.")
            else:
                # Reload the metadata to get the nostrmedia URL
                if os.path.exists(metadata_file):
                    metadata = load_json_file(metadata_file)
                    if 'platforms' in metadata and 'nostrmedia' in metadata['platforms']:
                        nostrmedia_data = metadata['platforms']['nostrmedia']
                        if 'url' in nostrmedia_data:
                            metadata['nostrmedia_url'] = nostrmedia_data['url']
                            print(f"Successfully uploaded to nostrmedia: {metadata['nostrmedia_url']}")

        # Upload the video to Nostr
        result = upload_to_nostr(video_file, metadata, args.private_key, debug=args.debug)

        if result['success']:
            # Create platform-specific directory for nostr
            nostr_dir = get_platform_dir(video_dir, 'nostr')

            # Create nostr-specific metadata
            nostr_metadata = {
                'event_id': result['event_id'],
                'pubkey': result['pubkey'],
                'nostr_uri': result['nostr_uri'],
                'links': result['links'],
                'uploaded_at': datetime.now().isoformat()
            }

            # Save nostr-specific metadata
            nostr_metadata_file = os.path.join(nostr_dir, 'metadata.json')
            save_json_file(nostr_metadata_file, nostr_metadata)

            # Update main metadata to include the nostr platform
            main_metadata_file = os.path.join(video_dir, 'metadata.json')
            if os.path.exists(main_metadata_file):
                main_metadata = load_json_file(main_metadata_file)

                # Initialize platforms dict if it doesn't exist
                if 'platforms' not in main_metadata:
                    main_metadata['platforms'] = {}

                # Add nostr platform
                main_metadata['platforms']['nostr'] = {
                    'event_id': result['event_id'],
                    'pubkey': result['pubkey'],
                    'nostr_uri': result['nostr_uri'],
                    'links': result['links'],
                    'uploaded_at': datetime.now().isoformat()
                }

                save_json_file(main_metadata_file, main_metadata)
                print(f"Updated metadata with Nostr event information")

            return 0
        else:
            print(f"Error uploading to Nostr: {result['error']}")
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
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
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
        default=get_default_video_quality(),
        help='Video quality (e.g., best, 720p, etc.)'
    )
    download_parser.add_argument(
        '--delay',
        type=int,
        default=get_default_download_delay(),
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
        help='Private key string (hex or nsec format, if not provided, will use from config or generate a new one)'
    )
    nostrmedia_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output for nostrmedia upload'
    )

    # Create the parser for the "nostr" command
    nostr_parser = subparsers.add_parser(
        'nostr',
        help='Upload videos to the Nostr network'
    )
    nostr_parser.add_argument(
        'video_id',
        type=str,
        help='ID of the video to upload'
    )
    nostr_parser.add_argument(
        '--private-key',
        type=str,
        help='Private key string (hex or nsec format, if not provided, will use from config)'
    )
    nostr_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output for Nostr upload'
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
    elif args.command == 'nostr':
        return nostr_command(args)
    else:
        parser.print_help()
        return 0

if __name__ == '__main__':
    sys.exit(main())

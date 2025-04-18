"""
Nostrmedia command for nosvid CLI
"""

import os
from datetime import datetime
from .base import get_channel_title
from ...utils.filesystem import setup_directory_structure, get_platform_dir
from ...platforms.youtube import find_youtube_video_file
from ...platforms.nostrmedia import upload_video_to_nostrmedia, update_nostrmedia_metadata
from ...metadata.common import get_main_metadata, update_main_metadata, update_platform_metadata

def nostrmedia_command(args):
    """
    Upload videos to nostrmedia.com

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        channel_title = get_channel_title()
        print(f"Channel title: {channel_title}")

        # Set up directory structure
        dirs = setup_directory_structure(args.output_dir, channel_title)

        # Get the video directory
        video_dir = os.path.join(dirs['videos_dir'], args.video_id)

        # Get the YouTube platform directory
        youtube_dir = get_platform_dir(video_dir, 'youtube')

        # Load the metadata
        metadata = get_main_metadata(video_dir)
        if not metadata:
            print(f"Metadata file not found for video: {args.video_id}")
            return 1

        # Check if the video has been downloaded
        if 'platforms' not in metadata or 'youtube' not in metadata['platforms'] or not metadata['platforms']['youtube'].get('downloaded', False):
            print(f"Video has not been downloaded yet: {args.video_id}")
            return 1

        # Find the video file
        video_file = find_youtube_video_file(video_dir)
        if not video_file:
            print(f"No video files found in: {youtube_dir}")
            return 1

        print(f"Found video file: {os.path.basename(video_file)}")

        # Upload the video to nostrmedia
        result = upload_video_to_nostrmedia(video_file, args.private_key, debug=args.debug)

        # Add timestamp to the result
        result['uploaded_at'] = datetime.now().isoformat()

        if result['success']:
            # Create nostrmedia-specific metadata
            nostrmedia_metadata = {
                'url': result['url'],
                'hash': result['hash'],
                'uploaded_at': result['uploaded_at']
            }

            # Save nostrmedia-specific metadata
            update_nostrmedia_metadata(video_dir, nostrmedia_metadata)

            # Update main metadata to include the nostrmedia platform
            main_metadata = get_main_metadata(video_dir)
            main_metadata = update_platform_metadata(main_metadata, 'nostrmedia', nostrmedia_metadata)
            update_main_metadata(video_dir, main_metadata)

            return 0
        else:
            print(f"Error uploading to nostrmedia: {result['error']}")
            return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def register_nostrmedia_parser(subparsers):
    """
    Register the nostrmedia command parser

    Args:
        subparsers: Subparsers object from argparse
    """
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

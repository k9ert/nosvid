"""
Nostrmedia command for nosvid CLI
"""

import os
from datetime import datetime
from .base import get_channel_title
from ...utils.filesystem import setup_directory_structure, get_platform_dir, load_json_file, save_json_file
from ...nostrmedia.upload import upload_to_nostrmedia

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
        metadata_file = os.path.join(video_dir, 'metadata.json')
        if not os.path.exists(metadata_file):
            print(f"Metadata file not found: {metadata_file}")
            return 1

        metadata = load_json_file(metadata_file)

        # Check if the video has been downloaded
        if 'platforms' not in metadata or 'youtube' not in metadata['platforms'] or not metadata['platforms']['youtube'].get('downloaded', False):
            print(f"Video has not been downloaded yet: {args.video_id}")
            return 1

        # Find the video file
        video_files = []
        for file in os.listdir(youtube_dir):
            if file.endswith('.mp4') or file.endswith('.webm') or file.endswith('.mkv'):
                video_files.append(os.path.join(youtube_dir, file))

        if not video_files:
            print(f"No video files found in: {youtube_dir}")
            return 1

        # Use the first video file
        video_file = video_files[0]
        print(f"Found video file: {os.path.basename(video_file)}")

        # Upload the video to nostrmedia
        result = upload_to_nostrmedia(video_file, args.private_key, debug=args.debug)

        # Add timestamp to the result
        result['uploaded_at'] = datetime.now().isoformat()

        if result['success']:
            # Create platform-specific directory for nostrmedia
            nostrmedia_dir = get_platform_dir(video_dir, 'nostrmedia')

            # Create nostrmedia-specific metadata
            nostrmedia_metadata = {
                'url': result['url'],
                'hash': result['hash'],
                'uploaded_at': result['uploaded_at']
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
                main_metadata['platforms']['nostrmedia'] = nostrmedia_metadata

                save_json_file(main_metadata_file, main_metadata)

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

"""
Nostr command for nosvid CLI
"""

import os
from datetime import datetime
from .base import get_channel_title
from ...utils.filesystem import get_platform_dir, load_json_file, save_json_file, setup_directory_structure
from ...nostr.upload import upload_to_nostr
from ...metadata.list import list_videos
from .nostrmedia import nostrmedia_command

def nostr_command(args):
    """
    Upload videos to the Nostr network

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        channel_title = get_channel_title()
        print(f"Channel title: {channel_title}")

        # If no video ID is provided, find the oldest video that hasn't been posted to Nostr yet
        if not args.video_id:
            print("No video ID provided, finding the oldest not posted video...")

            # Set up directory structure
            dirs = setup_directory_structure(args.output_dir, channel_title)

            # List all videos
            videos, _ = list_videos(
                videos_dir=dirs['videos_dir'],
                metadata_dir=dirs['metadata_dir']
            )

            # Find the oldest video that hasn't been posted to Nostr
            oldest_not_posted = None
            for video in videos:
                # Check if the video has been downloaded
                if not video['downloaded']:
                    continue

                # Check if the video has been posted to Nostr
                if video.get('nostr_post_count', 0) > 0:
                    continue

                # This video hasn't been posted to Nostr yet
                oldest_not_posted = video
                break

            if not oldest_not_posted:
                print("No videos found that haven't been posted to Nostr yet.")
                return 0

            args.video_id = oldest_not_posted['video_id']
            print(f"Found oldest not posted video: {args.video_id}")

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

        # Find the description file
        description_file = None
        for file in os.listdir(youtube_dir):
            if file.endswith('.description'):
                description_file = os.path.join(youtube_dir, file)
                break

        if description_file:
            print(f"Found description file: {os.path.basename(description_file)}")
            try:
                with open(description_file, 'r', encoding='utf-8') as f:
                    metadata['description'] = f.read()
            except Exception as e:
                print(f"Warning: Could not read description file: {e}")

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

            # Save nostr-specific metadata with a unique filename based on the event ID
            event_id = result['event_id']
            nostr_metadata_file = os.path.join(nostr_dir, f"{event_id}.json")
            save_json_file(nostr_metadata_file, nostr_metadata)

            # Also save to the standard metadata.json for backward compatibility
            standard_metadata_file = os.path.join(nostr_dir, 'metadata.json')
            save_json_file(standard_metadata_file, nostr_metadata)

            # Update main metadata to include the nostr platform
            main_metadata_file = os.path.join(video_dir, 'metadata.json')
            if os.path.exists(main_metadata_file):
                main_metadata = load_json_file(main_metadata_file)

                # Initialize platforms dict if it doesn't exist
                if 'platforms' not in main_metadata:
                    main_metadata['platforms'] = {}

                # Initialize nostr posts array if it doesn't exist
                if 'nostr' not in main_metadata['platforms']:
                    main_metadata['platforms']['nostr'] = {
                        'posts': []
                    }

                # Create a new post entry
                post_entry = {
                    'event_id': result['event_id'],
                    'pubkey': result['pubkey'],
                    'nostr_uri': result['nostr_uri'],
                    'links': result['links'],
                    'uploaded_at': datetime.now().isoformat()
                }

                # Add the new post to the posts array
                main_metadata['platforms']['nostr']['posts'].append(post_entry)

                # Sort posts by uploaded_at timestamp (newest first)
                main_metadata['platforms']['nostr']['posts'].sort(
                    key=lambda post: post.get('uploaded_at', ''),
                    reverse=True
                )

                save_json_file(main_metadata_file, main_metadata)
                print(f"Updated metadata with Nostr event information")

            return 0
        else:
            print(f"Error uploading to Nostr: {result['error']}")
            return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def register_nostr_parser(subparsers):
    """
    Register the nostr command parser

    Args:
        subparsers: Subparsers object from argparse
    """
    nostr_parser = subparsers.add_parser(
        'nostr',
        help='Upload videos to the Nostr network'
    )
    nostr_parser.add_argument(
        'video_id',
        type=str,
        nargs='?',
        help='ID of the video to upload (if not specified, upload the oldest not posted video)'
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

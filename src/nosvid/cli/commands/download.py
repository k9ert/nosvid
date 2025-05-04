"""
Download command for nosvid CLI
"""

import time

from ...download.video import download_all_pending, download_video
from ...metadata.list import list_videos
from ...utils.config import get_default_download_delay, get_default_video_quality
from ...utils.filesystem import setup_directory_structure
from ...utils.find_oldest import find_oldest_not_downloaded
from .base import get_channel_title


def download_command(args):
    """
    Download videos

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        channel_title = get_channel_title()
        print(f"Channel title: {channel_title}")

        # If a specific video ID is provided, download only that video
        if args.video_id:
            print(f"Downloading video: {args.video_id}")
            # Set up directory structure
            dirs = setup_directory_structure(args.output_dir, channel_title)
            result = download_video(
                video_id=args.video_id,
                videos_dir=dirs["videos_dir"],
                quality=args.quality,
            )
            if result:
                print(f"Successfully downloaded video: {args.video_id}")
                return 0
            else:
                print(f"Failed to download video: {args.video_id}")
                return 1

        # If --all-pending is specified, download all pending videos
        if args.all_pending:
            print(f"Downloading all pending videos for channel: {channel_title}")

            # Set up directory structure
            dirs = setup_directory_structure(args.output_dir, channel_title)

            # List all videos
            videos, _ = list_videos(
                videos_dir=dirs["videos_dir"],
                metadata_dir=dirs["metadata_dir"],
                show_downloaded=False,
                show_not_downloaded=True,
            )

            # Download each video
            for video in videos:
                video_id = video["video_id"]
                print(f"Downloading video: {video_id}")
                result = download_video(
                    video_id=video_id,
                    videos_dir=dirs["videos_dir"],
                    quality=args.quality,
                )
                if result:
                    print(f"Successfully downloaded video: {video_id}")
                else:
                    print(f"Failed to download video: {video_id}")

                # Add a delay between downloads
                if args.delay > 0:
                    print(f"Waiting {args.delay} seconds before next download...")
                    time.sleep(args.delay)

            return 0

        # Otherwise, download the oldest pending video
        print(f"Downloading the oldest pending video for channel: {channel_title}")

        # Set up directory structure
        dirs = setup_directory_structure(args.output_dir, channel_title)

        # List all videos
        videos, _ = list_videos(
            videos_dir=dirs["videos_dir"],
            metadata_dir=dirs["metadata_dir"],
            show_downloaded=False,
            show_not_downloaded=True,
        )

        # If there are no pending videos, return
        if not videos:
            print("No pending videos to download.")
            return 0

        # Get the oldest video
        oldest_video = videos[0]
        video_id = oldest_video["video_id"]

        print(f"Downloading oldest pending video: {video_id}")
        result = download_video(
            video_id=video_id, videos_dir=dirs["videos_dir"], quality=args.quality
        )
        if result:
            print(f"Successfully downloaded video: {video_id}")
            return 0
        else:
            print(f"Failed to download video: {video_id}")
            return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


def register_download_parser(subparsers):
    """
    Register the download command parser

    Args:
        subparsers: Subparsers object from argparse
    """
    download_parser = subparsers.add_parser("download", help="Download videos")
    download_parser.add_argument(
        "video_id",
        type=str,
        nargs="?",
        help="ID of the video to download (if not specified, download the oldest pending video)",
    )
    download_parser.add_argument(
        "--all-pending",
        action="store_true",
        help="Download all videos that haven't been downloaded yet",
    )
    download_parser.add_argument(
        "--quality",
        type=str,
        default=get_default_video_quality(),
        help="Video quality (e.g., best, 720p, etc.)",
    )
    download_parser.add_argument(
        "--delay",
        type=int,
        default=get_default_download_delay(),
        help="Delay between downloads in seconds",
    )

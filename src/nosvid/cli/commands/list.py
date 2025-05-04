"""
List command for nosvid CLI
"""

from ...metadata.list import list_videos, print_video_list
from ...utils.filesystem import setup_directory_structure
from .base import CHANNEL_MAPPING, get_channel_title


def list_command(args):
    """
    List videos in the repository

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        channel_title = get_channel_title()
        print(f"Channel title: {channel_title}")

        # Determine which videos to show
        show_downloaded = True
        show_not_downloaded = True

        if args.downloaded:
            show_not_downloaded = False

        if args.not_downloaded:
            show_downloaded = False

        # Set up directory structure
        dirs = setup_directory_structure(args.output_dir, channel_title)

        # Get the channel ID from the mapping
        # For now, we're using the hardcoded channel ID for Einundzwanzig
        channel_id = "UCxSRxq14XIoMbFDEjMOPU5Q"  # Einundzwanzig Podcast

        # List the videos
        videos, stats = list_videos(
            videos_dir=dirs["videos_dir"],
            metadata_dir=dirs["metadata_dir"],
            channel_id=channel_id,
            show_downloaded=show_downloaded,
            show_not_downloaded=show_not_downloaded,
        )

        # Print the videos
        print_video_list(videos, stats)

        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


def register_list_parser(subparsers):
    """
    Register the list command parser

    Args:
        subparsers: Subparsers object from argparse
    """
    list_parser = subparsers.add_parser("list", help="List videos in the repository")
    list_parser.add_argument(
        "--downloaded", action="store_true", help="Show only downloaded videos"
    )
    list_parser.add_argument(
        "--not-downloaded",
        action="store_true",
        help="Show only videos that have not been downloaded",
    )

"""
Consistency check command for nosvid CLI
"""

import logging

from ...consistency import ConsistencyChecker
from .base import get_channel_title


def consistency_check_command(args):
    """
    Check consistency of the video repository in multiple stages:

    1. Check metadata.json files for all videos
    2. Verify video directories against channel_videos JSON files
    3. Verify MP4 files against metadata (check if MP4 exists but metadata doesn't indicate it's downloaded)

    When run with --fix, this command will:
    - Recreate missing metadata.json files
    - Update inconsistent metadata.json files
    - Delete video directories that don't exist in channel_videos JSON files
    - Update metadata to indicate videos are downloaded when MP4 files exist

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        # Configure logging
        log_level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logger = logging.getLogger("nosvid.consistency")

        channel_title = get_channel_title()
        logger.info(f"Channel title: {channel_title}")

        # Create and run the consistency checker
        checker = ConsistencyChecker(args.output_dir, channel_title, logger)
        checker.check(fix_issues=args.fix)

        # The summary is already printed by the ConsistencyChecker

        return 0
    except Exception as e:
        logging.error(f"Error: {str(e)}", exc_info=True)
        return 1


def register_consistency_check_parser(subparsers):
    """
    Register the consistency-check command parser

    Args:
        subparsers: Subparsers object from argparse
    """
    consistency_check_parser = subparsers.add_parser(
        "consistency-check",
        help="Check consistency of the video repository in multiple stages",
    )
    consistency_check_parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix inconsistencies (recreate metadata files, update inconsistent metadata, delete invalid directories)",
    )
    consistency_check_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

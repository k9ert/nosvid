"""
Consistency check command for nosvid CLI
"""

import logging
from .base import get_channel_title
from ...consistency import ConsistencyChecker

def consistency_check_command(args):
    """
    Check consistency of metadata.json files for all videos

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
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger('nosvid.consistency')

        channel_title = get_channel_title()
        logger.info(f"Channel title: {channel_title}")

        # Create and run the consistency checker
        checker = ConsistencyChecker(args.output_dir, channel_title, logger)
        result = checker.check(fix_issues=args.fix)

        # Print summary
        inconsistencies = result['inconsistencies']
        total = result['total']
        if inconsistencies > 0:
            percentage = (inconsistencies / total) * 100 if total > 0 else 0
            logger.info(f"\nSummary: {inconsistencies} inconsistencies found in {total} videos ({percentage:.1f}%)")
            if args.fix:
                logger.info("All inconsistencies have been fixed.")
            else:
                logger.info("Run with --fix to fix these inconsistencies.")
        else:
            logger.info(f"\nSummary: No inconsistencies found in {total} videos. Repository is consistent!")

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
        'consistency-check',
        help='Check consistency of metadata.json files for all videos'
    )
    consistency_check_parser.add_argument(
        '--fix',
        action='store_true',
        help='Fix inconsistencies'
    )
    consistency_check_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

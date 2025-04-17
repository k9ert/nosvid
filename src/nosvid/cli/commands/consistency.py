"""
Consistency check command for nosvid CLI
"""

from .base import get_channel_title
from ...utils.consistency import check_metadata_consistency

def consistency_check_command(args):
    """
    Check consistency of metadata.json files for all videos

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        channel_title = get_channel_title()
        print(f"Channel title: {channel_title}")

        # Run the consistency check
        result = check_metadata_consistency(args.output_dir, channel_title, args.fix)

        # Print the results
        print("\nConsistency check completed!")
        print(f"Total videos: {result['total']}")
        print(f"Videos checked: {result['checked']}")
        print(f"Inconsistencies found: {result['inconsistencies']}")

        if result['inconsistencies'] > 0:
            print("\nInconsistencies:")
            for i, issue in enumerate(result['issues'], 1):
                print(f"{i}. {issue}")

        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
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

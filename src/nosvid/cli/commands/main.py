"""
Main module for nosvid CLI commands
"""

import sys
import argparse
from ...utils.config import get_default_output_dir
from .sync import sync_command, register_sync_parser
from .list import list_command, register_list_parser
from .download import download_command, register_download_parser
from .nostrmedia import nostrmedia_command, register_nostrmedia_parser
from .nostr import nostr_command, register_nostr_parser
from .consistency import consistency_check_command, register_consistency_check_parser
from .serve import serve_command, add_serve_command

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

    # Register command parsers
    register_sync_parser(subparsers)
    register_list_parser(subparsers)
    register_download_parser(subparsers)
    register_nostrmedia_parser(subparsers)
    register_nostr_parser(subparsers)
    register_consistency_check_parser(subparsers)
    add_serve_command(subparsers)

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
    elif args.command == 'consistency-check':
        return consistency_check_command(args)
    elif args.command == 'serve':
        return serve_command(args)
    else:
        parser.print_help()
        return 0

if __name__ == '__main__':
    sys.exit(main())

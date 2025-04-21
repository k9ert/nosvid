#!/usr/bin/env python3
"""
Simple script to run a DecData node.

This script demonstrates how to create and run a DecData node.
"""

import os
import sys
import time
import argparse
from decdata.decdata_node import DecDataNode

def main():
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description='Run a DecData node')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=2122, help='Port to bind to')
    parser.add_argument('--share-dir', type=str, help='Directory containing videos to share')
    parser.add_argument('--nosvid-repo', type=str, help='Path to NosVid repository')
    parser.add_argument('--nosvid-api-url', type=str, default='http://localhost:2121/api', help='URL of the NosVid API')
    parser.add_argument('--channel-title', type=str, default='Einundzwanzig Podcast', help='Title of the channel')
    parser.add_argument('--sync-interval', type=int, default=300, help='Interval in seconds for syncing with NosVid API')
    parser.add_argument('--max-connections', type=int, default=0, help='Maximum number of connections (0 for unlimited)')

    args = parser.parse_args()

    # Create share directory if it doesn't exist
    if args.share_dir and not os.path.exists(args.share_dir):
        os.makedirs(args.share_dir, exist_ok=True)

    # Create and start the node
    node = DecDataNode(
        host=args.host,
        port=args.port,
        share_dir=args.share_dir,
        nosvid_repo=args.nosvid_repo,
        nosvid_api_url=args.nosvid_api_url,
        channel_title=args.channel_title,
        max_connections=args.max_connections,
        sync_interval=args.sync_interval
    )

    node.start()

    print(f"DecData node started on {args.host}:{args.port}")
    print("Press Ctrl+C to stop the node")

    try:
        # Keep the node running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping node...")
        node.stop()
        node.join()
        print("Node stopped")

if __name__ == '__main__':
    main()

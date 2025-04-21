#!/usr/bin/env python3
"""
Simple script to connect to a DecData node.

This script demonstrates how to create a node and connect to another node.
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
    parser = argparse.ArgumentParser(description='Connect to a DecData node')
    parser.add_argument('--host', type=str, required=True, help='Host to connect to')
    parser.add_argument('--port', type=int, required=True, help='Port to connect to')
    parser.add_argument('--local-port', type=int, default=0, help='Local port to bind to (0 for auto-assign)')
    parser.add_argument('--share-dir', type=str, help='Directory containing videos to share')
    parser.add_argument('--nosvid-repo', type=str, help='Path to NosVid repository')
    parser.add_argument('--nosvid-api-url', type=str, default='http://localhost:2121/api', help='URL of the NosVid API')
    parser.add_argument('--channel-title', type=str, default='Einundzwanzig Podcast', help='Title of the channel')

    args = parser.parse_args()

    # Create share directory if it doesn't exist
    if args.share_dir and not os.path.exists(args.share_dir):
        os.makedirs(args.share_dir, exist_ok=True)

    # Create and start the node
    node = DecDataNode(
        host='0.0.0.0',
        port=args.local_port,
        share_dir=args.share_dir,
        nosvid_repo=args.nosvid_repo,
        nosvid_api_url=args.nosvid_api_url,
        channel_title=args.channel_title
    )

    node.start()

    print(f"DecData node started on port {node.port}")

    # Connect to the remote node
    print(f"Connecting to {args.host}:{args.port}...")
    if node.connect_with_node(args.host, args.port):
        print(f"Connected to {args.host}:{args.port}")

        # Keep the connection open for a while
        try:
            print("Press Ctrl+C to disconnect")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Disconnecting...")
    else:
        print(f"Failed to connect to {args.host}:{args.port}")

    # Stop the node
    node.stop()
    node.join()
    print("Node stopped")

if __name__ == '__main__':
    main()

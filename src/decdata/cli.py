#!/usr/bin/env python3
"""
Command-line interface for the DecData node.

This module provides a command-line interface for interacting with the DecData node,
allowing users to start a node, connect to other nodes, search for videos, and download videos.
"""

import os
import sys
import time
import argparse
from .decdata_node import DecDataNode


def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='DecData - Decentralized Video Data Exchange')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start a DecData node')
    start_parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    start_parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    start_parser.add_argument('--share-dir', type=str, help='Directory containing videos to share')
    start_parser.add_argument('--nosvid-repo', type=str, help='Path to NosVid repository')
    start_parser.add_argument('--max-connections', type=int, default=0, help='Maximum number of connections (0 for unlimited)')
    
    # Connect command
    connect_parser = subparsers.add_parser('connect', help='Connect to another node')
    connect_parser.add_argument('--host', type=str, required=True, action='append', help='Host to connect to')
    connect_parser.add_argument('--port', type=int, required=True, action='append', help='Port to connect to')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for videos')
    search_parser.add_argument('query', type=str, nargs='?', help='Search query')
    search_parser.add_argument('--id', type=str, help='Video ID to search for')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download a video')
    download_parser.add_argument('video_id', type=str, help='ID of the video to download')
    download_parser.add_argument('--node', type=str, help='ID of the node to download from')
    download_parser.add_argument('--output', type=str, help='Output directory')
    
    return parser.parse_args()


def start_node(args):
    """
    Start a DecData node.
    
    Args:
        args: Command-line arguments
    """
    # Create and start the node
    node = DecDataNode(
        host=args.host,
        port=args.port,
        share_dir=args.share_dir,
        nosvid_repo=args.nosvid_repo,
        max_connections=args.max_connections
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


def connect_to_nodes(node, hosts, ports):
    """
    Connect to other nodes.
    
    Args:
        node: The DecData node
        hosts: List of hosts to connect to
        ports: List of ports to connect to
    """
    if len(hosts) != len(ports):
        print("Error: Number of hosts and ports must match")
        return
    
    for i in range(len(hosts)):
        host = hosts[i]
        port = ports[i]
        
        print(f"Connecting to {host}:{port}...")
        if node.connect_with_node(host, port):
            print(f"Connected to {host}:{port}")
        else:
            print(f"Failed to connect to {host}:{port}")


def search_videos(node, query=None, video_id=None):
    """
    Search for videos.
    
    Args:
        node: The DecData node
        query: Search query string
        video_id: Specific video ID to search for
    """
    if not query and not video_id:
        print("Error: Either query or video ID must be provided")
        return
    
    search_id = node.search_videos(query, video_id)
    print(f"Search request sent (ID: {search_id})")
    print("Waiting for results...")
    
    # Wait for results (in a real application, this would be handled asynchronously)
    time.sleep(5)
    
    print("Search complete")


def download_video(node, video_id, node_id=None, output_dir=None):
    """
    Download a video.
    
    Args:
        node: The DecData node
        video_id: ID of the video to download
        node_id: ID of the node to download from (optional)
        output_dir: Output directory (optional)
    """
    if output_dir:
        # Override share directory for this download
        original_share_dir = node.share_dir
        node.share_dir = output_dir
    
    request_id = node.download_video(video_id, node_id)
    
    if not request_id:
        print(f"Failed to download video {video_id}")
        return
    
    print(f"Download request sent (ID: {request_id})")
    print("Waiting for download to complete...")
    
    # Wait for download to complete (in a real application, this would be handled asynchronously)
    while request_id in node.active_transfers:
        transfer = node.active_transfers[request_id]
        if transfer['status'] == 'completed':
            print(f"Download completed: {video_id}")
            break
        elif transfer['status'] == 'failed':
            print(f"Download failed: {video_id}")
            break
        
        time.sleep(1)
    
    if output_dir:
        # Restore original share directory
        node.share_dir = original_share_dir


def main():
    """
    Main entry point for the CLI.
    """
    args = parse_args()
    
    if args.command == 'start':
        start_node(args)
    elif args.command == 'connect':
        # Create a temporary node for connecting to other nodes
        node = DecDataNode('0.0.0.0', 0)  # Use port 0 to let the OS assign a port
        node.start()
        
        try:
            connect_to_nodes(node, args.host, args.port)
            
            # Keep the node running for a while to allow connections to establish
            time.sleep(5)
        finally:
            node.stop()
            node.join()
    elif args.command == 'search':
        # Create a temporary node for searching
        node = DecDataNode('0.0.0.0', 0)  # Use port 0 to let the OS assign a port
        node.start()
        
        try:
            # Connect to other nodes (would need to be configured)
            # connect_to_nodes(node, ['localhost'], [8000])
            
            search_videos(node, args.query, args.id)
        finally:
            node.stop()
            node.join()
    elif args.command == 'download':
        # Create a temporary node for downloading
        node = DecDataNode('0.0.0.0', 0, share_dir=args.output)  # Use port 0 to let the OS assign a port
        node.start()
        
        try:
            # Connect to other nodes (would need to be configured)
            # connect_to_nodes(node, ['localhost'], [8000])
            
            download_video(node, args.video_id, args.node, args.output)
        finally:
            node.stop()
            node.join()
    else:
        print("Error: No command specified")
        print("Use --help for usage information")
        sys.exit(1)


if __name__ == '__main__':
    main()

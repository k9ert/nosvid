#!/usr/bin/env python3
"""
Example application using the DecData node.

This module demonstrates how to use the DecData node in a simple application.
It creates a node, connects to other nodes, and provides a simple console interface
for interacting with the node.
"""

import os
import sys
import threading
import time

from .decdata_node import DecDataNode


class DecDataExample:
    """
    Example application using the DecData node.
    """

    def __init__(self, host="0.0.0.0", port=8000, share_dir=None, nosvid_repo=None):
        """
        Initialize the example application.

        Args:
            host: Host to bind to
            port: Port to bind to
            share_dir: Directory containing videos to share
            nosvid_repo: Path to NosVid repository
        """
        self.host = host
        self.port = port
        self.share_dir = share_dir
        self.nosvid_repo = nosvid_repo

        # Create the node
        self.node = DecDataNode(
            host=host, port=port, share_dir=share_dir, nosvid_repo=nosvid_repo
        )

        # Start the node
        self.node.start()
        print(f"DecData node started on {host}:{port}")

        # Search results
        self.search_results = {}

    def stop(self):
        """
        Stop the node.
        """
        print("Stopping node...")
        self.node.stop()
        self.node.join()
        print("Node stopped")

    def connect_to_node(self, host, port):
        """
        Connect to another node.

        Args:
            host: Host to connect to
            port: Port to connect to

        Returns:
            True if connected successfully, False otherwise
        """
        print(f"Connecting to {host}:{port}...")
        return self.node.connect_with_node(host, port)

    def search_videos(self, query=None, video_id=None):
        """
        Search for videos.

        Args:
            query: Search query string
            video_id: Specific video ID to search for

        Returns:
            Search ID
        """
        if not query and not video_id:
            print("Error: Either query or video ID must be provided")
            return None

        search_id = self.node.search_videos(query, video_id)
        print(f"Search request sent (ID: {search_id})")
        return search_id

    def download_video(self, video_id, node_id=None):
        """
        Download a video.

        Args:
            video_id: ID of the video to download
            node_id: ID of the node to download from (optional)

        Returns:
            Request ID
        """
        request_id = self.node.download_video(video_id, node_id)

        if not request_id:
            print(f"Failed to download video {video_id}")
            return None

        print(f"Download request sent (ID: {request_id})")
        return request_id

    def print_help(self):
        """
        Print help information.
        """
        print("\nDecData Example Application")
        print("---------------------------")
        print("Available commands:")
        print("  connect <host> <port>   - Connect to another node")
        print("  search <query>          - Search for videos by query")
        print("  searchid <video_id>     - Search for a specific video by ID")
        print("  download <video_id>     - Download a video")
        print("  list                    - List local videos")
        print("  peers                   - List connected peers")
        print("  help                    - Show this help information")
        print("  exit                    - Exit the application")

    def list_local_videos(self):
        """
        List local videos.
        """
        if not self.node.video_catalog:
            print("No local videos found")
            return

        print("\nLocal Videos:")
        print("-------------")
        for video_id, metadata in self.node.video_catalog.items():
            print(f"Video ID: {video_id}")
            print(f"  File: {metadata.get('file_path')}")
            print(f"  Size: {metadata.get('file_size')} bytes")
            print(f"  Hash: {metadata.get('file_hash')}")
            print()

    def list_peers(self):
        """
        List connected peers.
        """
        inbound_nodes = list(self.node.nodes_inbound)
        outbound_nodes = list(self.node.nodes_outbound)

        if not inbound_nodes and not outbound_nodes:
            print("No connected peers")
            return

        print("\nConnected Peers:")
        print("----------------")

        if inbound_nodes:
            print("Inbound connections:")
            for node in inbound_nodes:
                print(f"  Node ID: {node.id}")
                print(f"  Host: {node.host}:{node.port}")
                videos = self.node.peers_catalog.get(node.id, [])
                print(f"  Videos: {len(videos)}")
                print()

        if outbound_nodes:
            print("Outbound connections:")
            for node in outbound_nodes:
                print(f"  Node ID: {node.id}")
                print(f"  Host: {node.host}:{node.port}")
                videos = self.node.peers_catalog.get(node.id, [])
                print(f"  Videos: {len(videos)}")
                print()

    def run(self):
        """
        Run the example application.
        """
        self.print_help()

        try:
            while True:
                command = input("\n> ").strip()

                if not command:
                    continue

                parts = command.split()
                cmd = parts[0].lower()

                if cmd == "exit":
                    break
                elif cmd == "help":
                    self.print_help()
                elif cmd == "connect":
                    if len(parts) < 3:
                        print("Usage: connect <host> <port>")
                        continue

                    host = parts[1]
                    try:
                        port = int(parts[2])
                    except ValueError:
                        print("Error: Port must be a number")
                        continue

                    if self.connect_to_node(host, port):
                        print(f"Connected to {host}:{port}")
                    else:
                        print(f"Failed to connect to {host}:{port}")
                elif cmd == "search":
                    if len(parts) < 2:
                        print("Usage: search <query>")
                        continue

                    query = " ".join(parts[1:])
                    self.search_videos(query=query)
                elif cmd == "searchid":
                    if len(parts) < 2:
                        print("Usage: searchid <video_id>")
                        continue

                    video_id = parts[1]
                    self.search_videos(video_id=video_id)
                elif cmd == "download":
                    if len(parts) < 2:
                        print("Usage: download <video_id> [node_id]")
                        continue

                    video_id = parts[1]
                    node_id = parts[2] if len(parts) > 2 else None

                    self.download_video(video_id, node_id)
                elif cmd == "list":
                    self.list_local_videos()
                elif cmd == "peers":
                    self.list_peers()
                else:
                    print(f"Unknown command: {cmd}")
                    print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.stop()


def main():
    """
    Main entry point for the example application.
    """
    import argparse

    parser = argparse.ArgumentParser(description="DecData Example Application")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument(
        "--share-dir", type=str, help="Directory containing videos to share"
    )
    parser.add_argument("--nosvid-repo", type=str, help="Path to NosVid repository")

    args = parser.parse_args()

    app = DecDataExample(
        host=args.host,
        port=args.port,
        share_dir=args.share_dir,
        nosvid_repo=args.nosvid_repo,
    )

    app.run()


if __name__ == "__main__":
    main()

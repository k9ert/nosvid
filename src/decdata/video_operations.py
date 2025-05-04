#!/usr/bin/env python3
"""
Video Operations for DecData - Video-specific operations

This module provides video-specific operations for the DecData project.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional


class VideoOperations:
    """
    Video Operations for DecData.

    This class provides video-specific operations for the DecData project.
    """

    def __init__(self, node):
        """
        Initialize the Video Operations.

        Args:
            node: The DecData node this manager is associated with
        """
        self.node = node

    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a video.

        Args:
            video_id: ID of the video

        Returns:
            Dictionary containing video information, or None if not found
        """
        # Check local catalog first
        if video_id in self.node.video_catalog:
            return self.node.video_catalog[video_id]

        # Try to get from NosVid API
        video_info = self.node.nosvid_api.get_video(video_id)
        if video_info:
            return video_info

        # Try to get from peers
        for node_id, videos in self.node.peers_catalog.items():
            if video_id in videos:
                # Find the node
                target_node = None
                for node in self.node.nodes_outbound:
                    if node.id == node_id:
                        target_node = node
                        break

                for node in self.node.nodes_inbound:
                    if node.id == node_id:
                        target_node = node
                        break

                if target_node:
                    # Request video info
                    from .message_handlers import request_video_info

                    request_video_info(self.node, target_node, video_id)

                    # Wait for response (in a real application, this would be handled asynchronously)
                    # For now, just return None and let the caller handle it
                    return None

        return None

    def search_videos(self, query=None, video_id=None):
        """
        Search for videos across the network.

        Args:
            query: Search query string
            video_id: Specific video ID to search for

        Returns:
            Search ID for tracking results
        """
        search_id = hashlib.md5(
            f"{time.time()}-{query}-{video_id}".encode()
        ).hexdigest()

        search_message = {
            "type": "search",
            "search_id": search_id,
            "query": query,
            "video_id": video_id,
        }

        # Send search message to all connected nodes
        for node in self.node.nodes_outbound:
            self.node.send_to_node(node, json.dumps(search_message))

        for node in self.node.nodes_inbound:
            self.node.send_to_node(node, json.dumps(search_message))

        print(
            f"Sent search request to {len(self.node.nodes_outbound) + len(self.node.nodes_inbound)} nodes"
        )
        return search_id

    def download_video(self, video_id, node_id=None):
        """
        Download a video from the network.

        Args:
            video_id: ID of the video to download
            node_id: ID of the node to download from (optional)

        Returns:
            Request ID for tracking the download
        """
        # Check if we already have the video
        if video_id in self.node.video_catalog:
            print(f"Video {video_id} already in local catalog")
            return None

        # Try to download from NosVid API first
        if self.node.nosvid_api:
            try:
                print(f"Trying to download video {video_id} from NosVid API...")
                success = self.node.nosvid_api.download_video(video_id)

                if success:
                    print(
                        f"Successfully requested download of video {video_id} from NosVid API"
                    )
                    # The video will be added to the catalog during the next sync
                    return None
            except Exception as e:
                print(f"Error downloading video {video_id} from NosVid API: {e}")

        # If NosVid API download failed or not available, try to download from peers
        request_id = hashlib.md5(f"{time.time()}-{video_id}".encode()).hexdigest()

        download_message = {
            "type": "download_request",
            "request_id": request_id,
            "video_id": video_id,
        }

        # Find node that has the video
        target_node = None

        if node_id:
            # Find specific node
            for node in self.node.nodes_outbound:
                if node.id == node_id:
                    target_node = node
                    break

            for node in self.node.nodes_inbound:
                if node.id == node_id:
                    target_node = node
                    break
        else:
            # Find any node that has the video
            for node_id, videos in self.node.peers_catalog.items():
                if video_id in videos:
                    for node in self.node.nodes_outbound:
                        if node.id == node_id:
                            target_node = node
                            break

                    for node in self.node.nodes_inbound:
                        if node.id == node_id:
                            target_node = node
                            break

                    if target_node:
                        break

        if not target_node:
            print(f"No node found with video {video_id}")
            return None

        # Send download request
        self.node.send_to_node(target_node, json.dumps(download_message))
        print(f"Sent download request for video {video_id} to node {target_node.id}")

        # Track active transfer
        self.node.active_transfers[request_id] = {
            "video_id": video_id,
            "node_id": target_node.id,
            "start_time": time.time(),
            "status": "requested",
        }

        return request_id

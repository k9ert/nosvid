#!/usr/bin/env python3
"""
DecData Node - A peer-to-peer node for exchanging video data

This module implements a peer-to-peer node for the DecData project,
which enables decentralized exchange of video data collected by the NosVid project.
It integrates all components of the DecData system.
"""

import json
from typing import Dict, List, Any, Optional

from .base_node import BaseNode
from .catalog_manager import CatalogManager
from .video_operations import VideoOperations
from .message_handlers import (
    request_video_info,
    handle_search_message,
    handle_search_result_message,
    handle_download_request,
    handle_file_data,
    handle_video_info_request
)
from .message_handlers_part2 import handle_video_info_response


class DecDataNode(BaseNode):
    """
    DecData Node for peer-to-peer video data exchange.

    This class integrates all components of the DecData system.
    """

    def __init__(self, host: str, port: int,
                 nosvid_api_url: str = "http://localhost:2121/api",
                 id: str = None, max_connections: int = 0,
                 sync_interval: int = 300):
        """
        Initialize the DecData node.

        Args:
            host: The host name or ip address to bind to
            port: The port number to bind to
            nosvid_api_url: URL of the NosVid API
            id: Node ID (optional, will be generated if not provided)
            max_connections: Maximum number of connections (0 for unlimited)
            sync_interval: Interval in seconds for syncing with NosVid API
        """
        super(DecDataNode, self).__init__(host, port, nosvid_api_url, id, max_connections)

        # Initialize components
        self.catalog_manager = CatalogManager(self, sync_interval)
        self.video_operations = VideoOperations(self)

        print(f"DecDataNode: Started on {host}:{port}")

    def outbound_node_connected(self, node):
        """
        Event triggered when connected to another node.

        Args:
            node: The node that we connected to
        """
        super(DecDataNode, self).outbound_node_connected(node)
        self.catalog_manager.send_catalog_to_node(node)

    def inbound_node_connected(self, node):
        """
        Event triggered when another node connects to this node.

        Args:
            node: The node that connected to us
        """
        super(DecDataNode, self).inbound_node_connected(node)
        self.catalog_manager.send_catalog_to_node(node)

    def start(self):
        """
        Start the node and all its components.
        """
        super(DecDataNode, self).start()
        self.catalog_manager.start()

    def stop(self):
        """
        Stop the node and all its components.
        """
        self.catalog_manager.stop()
        super(DecDataNode, self).stop()

    def dispatch_message(self, node, message):
        """
        Dispatch a message to the appropriate handler based on its type.

        Args:
            node: The node that sent the message
            message: The parsed message
        """
        message_type = message.get('type')

        if message_type == 'catalog':
            self.catalog_manager.handle_catalog_message(node, message)
        elif message_type == 'search':
            handle_search_message(self, node, message)
        elif message_type == 'search_result':
            handle_search_result_message(self, node, message)
        elif message_type == 'download_request':
            handle_download_request(self, node, message)
        elif message_type == 'file_data':
            handle_file_data(self, node, message)
        elif message_type == 'video_info_request':
            handle_video_info_request(self, node, message)
        elif message_type == 'video_info_response':
            handle_video_info_response(self, node, message)
        elif message_type == 'message':
            # Handle simple message type for interactive mode
            print(f"Message from {node.id}: {message.get('content', '')}")
        else:
            print(f"Unknown message type: {message_type}")

    # Convenience methods that delegate to components

    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a video.

        Args:
            video_id: ID of the video

        Returns:
            Dictionary containing video information, or None if not found
        """
        return self.video_operations.get_video_info(video_id)

    def search_videos(self, query=None, video_id=None):
        """
        Search for videos across the network.

        Args:
            query: Search query string
            video_id: Specific video ID to search for

        Returns:
            Search ID for tracking results
        """
        return self.video_operations.search_videos(query, video_id)

    def download_video(self, video_id, node_id=None):
        """
        Download a video from the network.

        Args:
            video_id: ID of the video to download
            node_id: ID of the node to download from (optional)

        Returns:
            Request ID for tracking the download
        """
        return self.video_operations.download_video(video_id, node_id)

    def load_local_catalog(self):
        """
        Load the local video catalog from the NosVid API.
        """
        self.catalog_manager.load_local_catalog()

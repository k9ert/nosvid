#!/usr/bin/env python3
"""
Base Node for DecData - Core node functionality

This module provides the base node functionality for the DecData project,
extending the Node class from p2pnetwork.
"""

import json
import threading
import sys
from typing import Dict, List, Any, Callable
from p2pnetwork.node import Node
from pathlib import Path

# Add the parent directory to sys.path to allow importing nosvid modules
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from nosvid.utils.config import get_decdata_node_prefix
from .nosvid_api_client import NosVidAPIClient


class BaseNode(Node):
    """
    Base Node for DecData.

    This class extends the Node class from p2pnetwork to provide
    the core functionality needed for the DecData project.
    """

    def __init__(self, host: str, port: int,
                 nosvid_api_url: str = "http://localhost:2121/api",
                 id: str = None, max_connections: int = 0,
                 node_prefix_provider=None):
        """
        Initialize the Base Node.

        Args:
            host: The host name or ip address to bind to
            port: The port number to bind to
            nosvid_api_url: URL of the NosVid API
            id: Node ID (optional, will be generated if not provided)
            max_connections: Maximum number of connections (0 for unlimited)
            node_prefix_provider: Function that returns the node prefix (for testing)
        """
        # Get the node prefix from config or from the provided function
        if node_prefix_provider:
            prefix = node_prefix_provider()
        else:
            prefix = get_decdata_node_prefix()

        # Initialize the parent class with the original ID
        super(BaseNode, self).__init__(host, port, id, None, max_connections)

        # Store the original ID
        self.original_id = self.id

        # Format the ID with prefix and ensure it's exactly 30 characters
        if self.id:
            # Create the formatted ID with prefix
            formatted_id = f"{prefix}{self.original_id}"

            # If the formatted ID is longer than 30 characters, truncate it
            if len(formatted_id) > 30:
                self.id = formatted_id[:30]
            # If the formatted ID is shorter than 30 characters, pad it with zeros
            elif len(formatted_id) < 30:
                self.id = formatted_id.ljust(30, '0')
            else:
                self.id = formatted_id

        # NosVid API client
        self.nosvid_api = NosVidAPIClient(nosvid_api_url)

        # Video catalog - maps video_id to metadata
        self.video_catalog: Dict[str, Dict[str, Any]] = {}

        # Peers catalog - maps node_id to available videos
        self.peers_catalog: Dict[str, List[str]] = {}

        # Active transfers
        self.active_transfers: Dict[str, Dict[str, Any]] = {}

        # Message handlers
        self.message_handlers: List[Callable] = []

        print(f"BaseNode: Started on {host}:{port} with ID {self.id}")

    def outbound_node_connected(self, node):
        """
        Event triggered when connected to another node.

        Args:
            node: The node that we connected to
        """
        print(f"Connected to node: {node.id}")

    def inbound_node_connected(self, node):
        """
        Event triggered when another node connects to this node.

        Args:
            node: The node that connected to us
        """
        print(f"Node connected: {node.id}")

    def inbound_node_disconnected(self, node):
        """
        Event triggered when a node disconnects from this node.

        Args:
            node: The node that disconnected
        """
        print(f"Node disconnected: {node.id}")
        if node.id in self.peers_catalog:
            del self.peers_catalog[node.id]

    def outbound_node_disconnected(self, node):
        """
        Event triggered when disconnected from another node.

        Args:
            node: The node we disconnected from
        """
        print(f"Disconnected from node: {node.id}")
        if node.id in self.peers_catalog:
            del self.peers_catalog[node.id]

    def add_message_handler(self, handler):
        """
        Add a message handler function.

        The handler function should have the signature:
        handler(node, peer, data)

        Args:
            handler: The handler function to add
        """
        if handler not in self.message_handlers:
            self.message_handlers.append(handler)
            print(f"Added message handler: {handler.__name__ if hasattr(handler, '__name__') else handler}")

    def node_message(self, node, data):
        """
        Event triggered when a message is received from a node.

        Args:
            node: The node that sent the message
            data: The message data
        """
        # Safely print the message preview
        try:
            if isinstance(data, str):
                preview = data[:100]
            elif isinstance(data, dict):
                preview = str(data)[:100]
            else:
                preview = str(data)[:100]
            print(f"Message from node {node.id}: {preview}...")
        except Exception as e:
            print(f"Message from node {node.id}: <error displaying message preview: {e}>")

        # Call all registered message handlers
        for handler in self.message_handlers:
            try:
                handler(self, node, data)
            except Exception as e:
                print(f"Error in message handler {handler.__name__ if hasattr(handler, '__name__') else handler}: {e}")

        try:
            # Handle different data types
            if isinstance(data, dict):
                message = data
            elif isinstance(data, str):
                message = json.loads(data)
            else:
                print(f"Unsupported data type: {type(data)}")
                return

            # Dispatch message to appropriate handler
            self.dispatch_message(node, message)

        except json.JSONDecodeError:
            print("Received invalid JSON data")
        except Exception as e:
            print(f"Error processing message: {e}")

    def dispatch_message(self, node, message):
        """
        Dispatch a message to the appropriate handler based on its type.
        This method should be overridden by subclasses.

        Args:
            node: The node that sent the message
            message: The parsed message
        """
        message_type = message.get('type')
        print(f"Received message of type: {message_type}")

    def get_peers(self):
        """
        Get a list of all connected peers.

        Returns:
            List of connected peer nodes
        """
        # Combine inbound and outbound nodes
        return self.nodes_inbound + self.nodes_outbound

"""
Integration tests for the DecData node.
"""

import os
from pathlib import Path

import pytest
import yaml

from decdata.decdata_node import DecDataNode


@pytest.mark.integration
class TestNodeIntegration:
    """Integration tests for the DecData node."""

    def test_node_creation_with_config(self, temp_config_file):
        """Test creating a node with a configuration file."""
        # Create a node with a specific ID
        test_id = "abcdef1234567890abcdef1234567890"
        node = DecDataNode(host="127.0.0.1", port=2122, id=test_id)

        try:
            # Check that the ID was formatted correctly
            assert node.id.startswith("test-node-")
            assert len(node.id) == 30  # Exactly 30 characters
            assert node.original_id == test_id
        finally:
            # Make sure to stop the node
            node.stop()

    def test_auto_generated_node_id(self, temp_config_file):
        """Test that an auto-generated node ID is formatted correctly."""
        # Create a node with an auto-generated ID
        node = DecDataNode(host="127.0.0.1", port=2123)

        try:
            # Check that the ID was formatted correctly
            assert node.id.startswith("test-node-")
            assert len(node.id) == 30  # Exactly 30 characters
            assert node.original_id is not None
        finally:
            # Make sure to stop the node
            node.stop()

    def test_node_connection(self, temp_config_file):
        """Test that nodes can connect to each other with formatted IDs."""
        # This test is marked as skip by default because it involves actual network connections
        pytest.skip(
            "This test involves actual network connections and is disabled by default"
        )

        # Create two nodes
        node1 = DecDataNode(host="127.0.0.1", port=2124)
        node2 = DecDataNode(host="127.0.0.1", port=2125)

        try:
            # Start the nodes
            node1.start()
            node2.start()

            # Connect node1 to node2
            connected = node1.connect_with_node("127.0.0.1", 2125)

            # Check that the connection was successful
            assert connected
            assert len(node1.nodes_outbound) == 1
            assert len(node2.nodes_inbound) == 1

            # Check that the node IDs are formatted correctly
            assert node1.id.startswith("test-node-")
            assert node2.id.startswith("test-node-")
            assert len(node1.id) == 30  # Exactly 30 characters
            assert len(node2.id) == 30  # Exactly 30 characters
        finally:
            # Make sure to stop the nodes
            node1.stop()
            node2.stop()

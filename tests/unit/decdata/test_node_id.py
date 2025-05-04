"""
Unit tests for the node ID formatting feature in DecData.
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the module to test
from decdata.base_node import BaseNode


@pytest.fixture
def node_prefix_provider():
    """
    Fixture to provide a configurable node prefix function.

    Returns a function that can be used to get and set the prefix value.
    """
    prefix_value = ['test-node-']  # Use a list to allow modification in nested functions

    def _get_prefix():
        return prefix_value[0]

    def _set_prefix(new_prefix):
        prefix_value[0] = new_prefix
        return _get_prefix

    # Set the initial value
    _get_prefix.set_prefix = _set_prefix

    return _get_prefix


@pytest.mark.unit
class TestNodeId:
    """Tests for the node ID formatting feature."""

    def test_node_id_with_provided_id(self, mock_p2p_node, node_prefix_provider):
        """Test that a provided node ID is formatted correctly."""
        # Create a node with a specific ID and inject the prefix provider
        test_id = "abcdef1234567890abcdef1234567890"
        node = BaseNode(
            host="127.0.0.1",
            port=2122,
            id=test_id,
            node_prefix_provider=node_prefix_provider
        )

        # Check that the ID was formatted correctly
        assert node.id.startswith('test-node-')
        assert len(node.id) == 30  # Exactly 30 characters
        assert node.original_id == test_id

    def test_node_id_with_generated_id(self, mock_p2p_node, node_prefix_provider, monkeypatch):
        """Test that an auto-generated node ID is formatted correctly."""
        # Mock the Node.generate_id method to return a predictable ID
        monkeypatch.setattr('p2pnetwork.node.Node.generate_id',
                           lambda _: "generated1234567890")

        # Create a node with an auto-generated ID and inject the prefix provider
        node = BaseNode(
            host="127.0.0.1",
            port=2123,
            node_prefix_provider=node_prefix_provider
        )

        # Check that the ID was formatted correctly
        assert node.id.startswith('test-node-')
        assert len(node.id) == 30  # Exactly 30 characters
        assert node.original_id is not None

    def test_node_id_with_custom_prefix(self, mock_p2p_node, node_prefix_provider):
        """Test that a custom prefix from config is used."""
        # Set the node prefix to a custom value
        node_prefix_provider.set_prefix('custom-prefix-')

        # Create a node with a specific ID and inject the prefix provider
        test_id = "abcdefghijklmnopqrstuvwxyz1234567890"
        node = BaseNode(
            host="127.0.0.1",
            port=2124,
            id=test_id,
            node_prefix_provider=node_prefix_provider
        )

        # Check that the ID was formatted with the custom prefix
        assert node.id.startswith('custom-prefix-')
        assert node.original_id == test_id

        # Check that the total length is exactly 30 characters
        assert len(node.id) == 30

    def test_node_id_length_limit(self, mock_p2p_node, node_prefix_provider):
        """Test that the node ID is limited to 30 characters even with a long prefix."""
        # Set the node prefix to a very long value
        node_prefix_provider.set_prefix('very-long-prefix-that-exceeds-limit-')

        # Create a node with a specific ID and inject the prefix provider
        test_id = "abcdefhijklmnopqrstuvwxyz1234567890"
        node = BaseNode(
            host="127.0.0.1",
            port=2125,
            id=test_id,
            node_prefix_provider=node_prefix_provider
        )

        # Check that the total length is exactly 30 characters
        assert len(node.id) == 30
        assert node.original_id == test_id

        # Check that the ID is truncated when the prefix is very long
        assert not node.id.endswith(test_id)

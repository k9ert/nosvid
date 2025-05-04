"""
Shared test fixtures for all tests.
"""

import os
import sys
import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_dir))


@pytest.fixture
def temp_config_file(tmp_path):
    """
    Create a temporary config.yaml file with test settings.

    Returns:
        Path to the temporary config file
    """
    config_path = tmp_path / "config.yaml"
    config = {
        'decdata': {
            'node_prefix': 'test-node-'
        }
    }

    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    # Store the original config path to restore later
    original_config = os.environ.get('NOSVID_CONFIG_PATH')

    # Set the environment variable to point to our test config
    os.environ['NOSVID_CONFIG_PATH'] = str(config_path)

    yield config_path

    # Restore the original config path
    if original_config:
        os.environ['NOSVID_CONFIG_PATH'] = original_config
    else:
        os.environ.pop('NOSVID_CONFIG_PATH', None)


@pytest.fixture
def mock_p2p_node(monkeypatch):
    """
    Mock the p2pnetwork.node.Node class to avoid network operations during tests.
    """
    # Create a mock for the Node class
    mock_node = MagicMock()

    # Mock the Node.__init__ method to just set attributes without networking
    def mock_init(self, host, port, id=None, callback=None, max_connections=0):
        self.host = host
        self.port = port
        self.id = id or "mock-node-id"
        self.callback = callback
        self.max_connections = max_connections
        self.nodes_inbound = []
        self.nodes_outbound = []
        self.terminate_flag = False

    # Apply the monkeypatch to the Node.__init__ method
    monkeypatch.setattr('p2pnetwork.node.Node.__init__', mock_init)

    # Mock other methods to do nothing
    monkeypatch.setattr('p2pnetwork.node.Node.start', lambda self: None)
    monkeypatch.setattr('p2pnetwork.node.Node.stop', lambda self: None)
    monkeypatch.setattr('p2pnetwork.node.Node.connect_with_node', lambda self, host, port: True)
    monkeypatch.setattr('p2pnetwork.node.Node.send_to_node', lambda self, node, data: None)

    return mock_node

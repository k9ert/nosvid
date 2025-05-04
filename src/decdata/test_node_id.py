#!/usr/bin/env python3
"""
Test script for the node ID formatting feature.
"""

import os
import sys
import yaml
from pathlib import Path

# Add the parent directory to sys.path to allow importing the decdata module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from decdata.decdata_node import DecDataNode

# Create a test config.yaml file with a custom node prefix
config_path = 'config.yaml'
if not os.path.exists(config_path):
    # Create a minimal config file for testing
    config = {
        'decdata': {
            'node_prefix': 'test-node-'
        }
    }
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    print(f"Created test config file at {config_path}")
else:
    # Check if the config file already has a decdata section
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) or {}
    
    if 'decdata' not in config:
        config['decdata'] = {'node_prefix': 'test-node-'}
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        print(f"Updated config file at {config_path}")
    elif 'node_prefix' not in config['decdata']:
        config['decdata']['node_prefix'] = 'test-node-'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        print(f"Added node_prefix to config file at {config_path}")
    else:
        print(f"Using existing node_prefix: {config['decdata']['node_prefix']}")

# Create a node with a specific ID
node1 = DecDataNode(host="127.0.0.1", port=2122, id="abcdef1234567890abcdef1234567890")
print(f"Node 1 ID: {node1.id}")
print(f"Node 1 Original ID: {node1.original_id}")

# Create a node with an auto-generated ID
node2 = DecDataNode(host="127.0.0.1", port=2123)
print(f"Node 2 ID: {node2.id}")
print(f"Node 2 Original ID: {node2.original_id}")

# Stop the nodes
node1.stop()
node2.stop()

print("\nTest completed successfully!")

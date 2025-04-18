"""
Tests for the ConfigService
"""

import unittest
import os
import tempfile
import yaml
from src.nosvid.services.config_service import ConfigService

class TestConfigService(unittest.TestCase):
    """Tests for the ConfigService"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create a temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.yaml')
        self.temp_file.close()
        
        # Create test config
        self.test_config = {
            'youtube': {
                'api_key': 'test_api_key'
            },
            'nostr': {
                'nsec': 'test_nsec',
                'npub': 'test_npub'
            },
            'defaults': {
                'output_dir': './test_repository'
            },
            'channel': {
                'title': 'TestChannel'
            }
        }
        
        # Write test config to file
        with open(self.temp_file.name, 'w') as f:
            yaml.dump(self.test_config, f)
        
        # Create config service
        self.config_service = ConfigService(self.temp_file.name)
    
    def tearDown(self):
        """Clean up the test environment"""
        # Remove the temporary config file
        os.unlink(self.temp_file.name)
    
    def test_get(self):
        """Test getting a configuration value"""
        # Test getting a top-level value
        self.assertEqual(self.config_service.get('youtube'), {'api_key': 'test_api_key'})
        
        # Test getting a nested value
        self.assertEqual(self.config_service.get('youtube.api_key'), 'test_api_key')
        
        # Test getting a value that doesn't exist
        self.assertIsNone(self.config_service.get('nonexistent'))
        
        # Test getting a value that doesn't exist with a default
        self.assertEqual(self.config_service.get('nonexistent', 'default'), 'default')
    
    def test_set(self):
        """Test setting a configuration value"""
        # Test setting a top-level value
        self.config_service.set('test', 'value')
        self.assertEqual(self.config_service.get('test'), 'value')
        
        # Test setting a nested value
        self.config_service.set('test.nested', 'nested_value')
        self.assertEqual(self.config_service.get('test.nested'), 'nested_value')
        
        # Test overwriting a value
        self.config_service.set('youtube.api_key', 'new_api_key')
        self.assertEqual(self.config_service.get('youtube.api_key'), 'new_api_key')
    
    def test_save(self):
        """Test saving configuration to file"""
        # Set a new value
        self.config_service.set('test', 'value')
        
        # Save the configuration
        self.config_service.save()
        
        # Load the configuration from file
        with open(self.temp_file.name, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check that the new value was saved
        self.assertEqual(config['test'], 'value')
    
    def test_get_api_key(self):
        """Test getting an API key"""
        self.assertEqual(self.config_service.get_api_key('youtube'), 'test_api_key')
        self.assertIsNone(self.config_service.get_api_key('nonexistent'))
    
    def test_get_nostr_key(self):
        """Test getting a Nostr key"""
        self.assertEqual(self.config_service.get_nostr_key('nsec'), 'test_nsec')
        self.assertEqual(self.config_service.get_nostr_key('npub'), 'test_npub')
        self.assertIsNone(self.config_service.get_nostr_key('nonexistent'))
    
    def test_get_output_dir(self):
        """Test getting the output directory"""
        self.assertEqual(self.config_service.get_output_dir(), './test_repository')
        
        # Test with default value
        self.config_service.set('defaults.output_dir', None)
        self.assertEqual(self.config_service.get_output_dir(), './repository')
    
    def test_get_channel_title(self):
        """Test getting the channel title"""
        self.assertEqual(self.config_service.get_channel_title(), 'TestChannel')
        
        # Test with default value
        self.config_service.set('channel.title', None)
        self.assertEqual(self.config_service.get_channel_title(), 'Einundzwanzig')

if __name__ == "__main__":
    unittest.main()

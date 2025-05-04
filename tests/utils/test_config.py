"""
Tests for the config utility functions
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import yaml

from src.nosvid.utils import config


class TestConfigUtils(unittest.TestCase):
    """Tests for the config utility functions"""

    def setUp(self):
        """Set up the test environment"""
        # Create a temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
        self.temp_file.close()

        # Create test config
        self.test_config = {
            "youtube": {"api_key": "test_api_key", "cookies_file": "~/cookies.txt"},
            "nostr": {
                "nsec": "test_nsec",
                "npub": "test_npub",
                "relays": ["wss://test.relay.com"],
            },
            "defaults": {
                "output_dir": "~/test_output",
                "video_quality": "high",
                "web_port": 8080,
                "download_delay": 10,
                "repository_dir": "./test_repository",
            },
            "decdata": {"node_prefix": "test-node-"},
        }

        # Write test config to file
        with open(self.temp_file.name, "w") as f:
            yaml.dump(self.test_config, f)

        # Save the original environment
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up the test environment"""
        # Remove the temporary config file
        os.unlink(self.temp_file.name)

        # Restore the original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_load_config(self):
        """Test loading configuration from file"""
        # Test loading from a specific file
        loaded_config = config.load_config(self.temp_file.name)
        self.assertEqual(loaded_config, self.test_config)

        # Test loading from environment variable
        os.environ["NOSVID_CONFIG_PATH"] = self.temp_file.name
        loaded_config = config.load_config()
        self.assertEqual(loaded_config, self.test_config)

        # Test loading from a non-existent file
        loaded_config = config.load_config("nonexistent.yaml")
        self.assertEqual(loaded_config, {})

    def test_read_api_key_from_yaml(self):
        """Test reading API key from YAML file"""
        # Test reading from config.yaml
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            api_key = config.read_api_key_from_yaml("youtube")
            self.assertEqual(api_key, "test_api_key")

        # Test handling exception in load_config
        with patch(
            "src.nosvid.utils.config.load_config",
            side_effect=Exception("Test exception"),
        ):
            # This should fall through to the next method (secrets.yaml)
            with patch("builtins.open", create=True) as mock_open:
                mock_open.side_effect = [
                    unittest.mock.mock_open(
                        read_data=yaml.dump({"youtube": {"api_key": "secret_api_key"}})
                    ).return_value
                ]
                api_key = config.read_api_key_from_yaml("youtube")
                self.assertEqual(api_key, "secret_api_key")

        # Test reading from secrets.yaml
        with patch("src.nosvid.utils.config.load_config", return_value={}), patch(
            "builtins.open", create=True
        ) as mock_open:
            mock_open.side_effect = [
                unittest.mock.mock_open(
                    read_data=yaml.dump({"youtube": {"api_key": "secret_api_key"}})
                ).return_value
            ]
            api_key = config.read_api_key_from_yaml("youtube")
            self.assertEqual(api_key, "secret_api_key")

        # Test reading from key file
        with patch("src.nosvid.utils.config.load_config", return_value={}), patch(
            "builtins.open", create=True
        ) as mock_open:
            # First open for secrets.yaml fails
            mock_open.side_effect = [
                FileNotFoundError,
                unittest.mock.mock_open(read_data="file_api_key").return_value,
            ]
            api_key = config.read_api_key_from_yaml("youtube", "youtube.key")
            self.assertEqual(api_key, "file_api_key")

        # Test reading from environment variable
        with patch("src.nosvid.utils.config.load_config", return_value={}), patch(
            "builtins.open", create=True
        ) as mock_open:
            # Both opens fail
            mock_open.side_effect = [FileNotFoundError, FileNotFoundError]
            os.environ["YOUTUBE_API_KEY"] = "env_api_key"
            api_key = config.read_api_key_from_yaml("youtube", "youtube.key")
            self.assertEqual(api_key, "env_api_key")

        # Test not finding the API key
        with patch("src.nosvid.utils.config.load_config", return_value={}), patch(
            "builtins.open", create=True
        ) as mock_open:
            # Both opens fail
            mock_open.side_effect = [FileNotFoundError, FileNotFoundError]
            # No environment variable
            if "YOUTUBE_API_KEY" in os.environ:
                del os.environ["YOUTUBE_API_KEY"]
            with self.assertRaises(FileNotFoundError):
                config.read_api_key_from_yaml("youtube", "youtube.key")

    def test_get_nostr_key(self):
        """Test getting a Nostr key"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting existing keys
            self.assertEqual(config.get_nostr_key("nsec"), "test_nsec")
            self.assertEqual(config.get_nostr_key("npub"), "test_npub")

            # Test getting a non-existent key
            self.assertIsNone(config.get_nostr_key("nonexistent"))

    def test_get_nostr_relays(self):
        """Test getting Nostr relays"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting relays from config
            self.assertEqual(config.get_nostr_relays(), ["wss://test.relay.com"])

        # Test getting default relays when not in config
        test_config_no_relays = self.test_config.copy()
        del test_config_no_relays["nostr"]["relays"]
        with patch(
            "src.nosvid.utils.config.load_config", return_value=test_config_no_relays
        ):
            relays = config.get_nostr_relays()
            self.assertIsInstance(relays, list)
            self.assertGreater(len(relays), 0)
            self.assertIn("wss://relay.damus.io", relays)

    def test_get_default_output_dir(self):
        """Test getting the default output directory"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting from config
            self.assertEqual(
                config.get_default_output_dir(), os.path.expanduser("~/test_output")
            )

        # Test getting default when not in config
        test_config_no_output = self.test_config.copy()
        del test_config_no_output["defaults"]["output_dir"]
        with patch(
            "src.nosvid.utils.config.load_config", return_value=test_config_no_output
        ):
            self.assertEqual(
                config.get_default_output_dir(),
                os.path.expanduser("~/Downloads/nosvid"),
            )

    def test_get_default_video_quality(self):
        """Test getting the default video quality"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting from config
            self.assertEqual(config.get_default_video_quality(), "high")

        # Test getting default when not in config
        test_config_no_quality = self.test_config.copy()
        del test_config_no_quality["defaults"]["video_quality"]
        with patch(
            "src.nosvid.utils.config.load_config", return_value=test_config_no_quality
        ):
            self.assertEqual(config.get_default_video_quality(), "best")

    def test_get_default_web_port(self):
        """Test getting the default web port"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting from config
            self.assertEqual(config.get_default_web_port(), 8080)

        # Test getting default when not in config
        test_config_no_port = self.test_config.copy()
        del test_config_no_port["defaults"]["web_port"]
        with patch(
            "src.nosvid.utils.config.load_config", return_value=test_config_no_port
        ):
            self.assertEqual(config.get_default_web_port(), 2121)

    def test_get_youtube_cookies_file(self):
        """Test getting the YouTube cookies file"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting from config
            self.assertEqual(
                config.get_youtube_cookies_file(), os.path.expanduser("~/cookies.txt")
            )

        # Test getting default when not in config
        test_config_no_cookies = self.test_config.copy()
        del test_config_no_cookies["youtube"]["cookies_file"]
        with patch(
            "src.nosvid.utils.config.load_config", return_value=test_config_no_cookies
        ):
            self.assertIsNone(config.get_youtube_cookies_file())

    def test_get_channel_id(self):
        """Test getting the channel ID"""
        # This is hardcoded, so just test the return value
        self.assertEqual(config.get_channel_id(), "UCxSRxq14XIoMbFDEjMOPU5Q")

    def test_get_default_download_delay(self):
        """Test getting the default download delay"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting from config
            self.assertEqual(config.get_default_download_delay(), 10)

        # Test getting default when not in config
        test_config_no_delay = self.test_config.copy()
        del test_config_no_delay["defaults"]["download_delay"]
        with patch(
            "src.nosvid.utils.config.load_config", return_value=test_config_no_delay
        ):
            self.assertEqual(config.get_default_download_delay(), 5)

    def test_get_youtube_api_key(self):
        """Test getting the YouTube API key"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting from config
            self.assertEqual(config.get_youtube_api_key(), "test_api_key")

        # Test getting default when not in config
        test_config_no_api_key = self.test_config.copy()
        del test_config_no_api_key["youtube"]["api_key"]
        with patch(
            "src.nosvid.utils.config.load_config", return_value=test_config_no_api_key
        ):
            self.assertIsNone(config.get_youtube_api_key())

    def test_get_repository_dir(self):
        """Test getting the repository directory"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting from config
            self.assertEqual(config.get_repository_dir(), "./test_repository")

        # Test getting default when not in config
        test_config_no_repo = self.test_config.copy()
        del test_config_no_repo["defaults"]["repository_dir"]
        with patch(
            "src.nosvid.utils.config.load_config", return_value=test_config_no_repo
        ):
            self.assertEqual(config.get_repository_dir(), "./repository")

    def test_get_decdata_node_prefix(self):
        """Test getting the DecData node prefix"""
        with patch(
            "src.nosvid.utils.config.load_config", return_value=self.test_config
        ):
            # Test getting from config
            self.assertEqual(config.get_decdata_node_prefix(), "test-node-")

        # Test getting default when not in config
        test_config_no_prefix = self.test_config.copy()
        del test_config_no_prefix["decdata"]["node_prefix"]
        with patch(
            "src.nosvid.utils.config.load_config", return_value=test_config_no_prefix
        ):
            self.assertEqual(config.get_decdata_node_prefix(), "node-")


if __name__ == "__main__":
    unittest.main()

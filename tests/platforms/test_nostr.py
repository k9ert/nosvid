"""
Tests for the Nostr platform module
"""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.nosvid.platforms import nostr


class TestNostrPlatform(unittest.TestCase):
    """Tests for the Nostr platform module"""

    def setUp(self):
        """Set up the test environment"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.video_dir = self.temp_dir.name

        # Create a nostr platform directory
        self.nostr_dir = os.path.join(self.video_dir, "platforms", "nostr")
        os.makedirs(self.nostr_dir, exist_ok=True)

        # Create test metadata
        self.test_metadata = {
            "event_id": "test_event_id",
            "pubkey": "test_pubkey",
            "nostr_uri": "nostr:test_uri",
            "links": {"web": "https://example.com"},
            "uploaded_at": "2023-01-01T12:00:00",
        }

        # Create additional test metadata
        self.additional_metadata = {
            "event_id": "additional_event_id",
            "pubkey": "additional_pubkey",
            "nostr_uri": "nostr:additional_uri",
            "links": {"web": "https://example2.com"},
            "uploaded_at": "2023-01-02T12:00:00",
        }

    def tearDown(self):
        """Clean up the test environment"""
        self.temp_dir.cleanup()

    def test_get_nostr_metadata_empty(self):
        """Test getting Nostr metadata when no metadata exists"""
        # Mock the filesystem functions
        with patch(
            "src.nosvid.platforms.nostr.get_platform_dir"
        ) as mock_get_dir, patch("os.path.exists", return_value=False):
            # Set up the mock return value
            mock_get_dir.return_value = self.nostr_dir

            # Test with no metadata file
            metadata = nostr.get_nostr_metadata(self.video_dir)
            self.assertEqual(metadata, {})

    def test_get_nostr_metadata(self):
        """Test getting Nostr metadata"""
        # Mock the filesystem functions
        with patch(
            "src.nosvid.platforms.nostr.get_platform_dir"
        ) as mock_get_dir, patch("os.path.exists", return_value=True), patch(
            "src.nosvid.platforms.nostr.load_json_file"
        ) as mock_load:
            # Set up the mock return values
            mock_get_dir.return_value = self.nostr_dir
            mock_load.return_value = self.test_metadata

            # Test getting the metadata
            metadata = nostr.get_nostr_metadata(self.video_dir)
            self.assertEqual(metadata, self.test_metadata)

            # Verify the mocks were called correctly
            mock_get_dir.assert_called_once_with(self.video_dir, "nostr")
            mock_load.assert_called_once_with(
                os.path.join(self.nostr_dir, "metadata.json")
            )

    def test_update_nostr_metadata(self):
        """Test updating Nostr metadata"""
        # Mock the filesystem functions
        with patch(
            "src.nosvid.platforms.nostr.get_platform_dir"
        ) as mock_get_dir, patch(
            "src.nosvid.platforms.nostr.save_json_file"
        ) as mock_save:
            # Set up the mock return value
            mock_get_dir.return_value = self.nostr_dir

            # Update the metadata
            nostr.update_nostr_metadata(self.video_dir, self.test_metadata)

            # Verify the mocks were called correctly
            mock_get_dir.assert_called_once_with(self.video_dir, "nostr")
            mock_save.assert_called_once_with(
                os.path.join(self.nostr_dir, "metadata.json"), self.test_metadata
            )

    def test_get_nostr_posts_empty(self):
        """Test getting Nostr posts when no posts exist"""
        # Mock the filesystem functions
        with patch(
            "src.nosvid.platforms.nostr.get_platform_dir"
        ) as mock_get_dir, patch("os.path.exists", return_value=False):
            # Set up the mock return value
            mock_get_dir.return_value = self.nostr_dir

            # Test with no posts
            posts = nostr.get_nostr_posts(self.video_dir)
            self.assertEqual(posts, [])

    def test_get_nostr_posts_with_metadata(self):
        """Test getting Nostr posts with metadata"""
        # Mock the filesystem functions
        with patch(
            "src.nosvid.platforms.nostr.get_platform_dir"
        ) as mock_get_dir, patch("os.path.exists", return_value=True), patch(
            "src.nosvid.platforms.nostr.load_json_file"
        ) as mock_load, patch(
            "os.listdir", return_value=["metadata.json"]
        ):
            # Set up the mock return values
            mock_get_dir.return_value = self.nostr_dir
            mock_load.return_value = self.test_metadata

            # Test getting the posts
            posts = nostr.get_nostr_posts(self.video_dir)
            self.assertEqual(len(posts), 1)
            self.assertEqual(posts[0]["event_id"], self.test_metadata["event_id"])
            self.assertEqual(posts[0]["pubkey"], self.test_metadata["pubkey"])
            self.assertEqual(posts[0]["nostr_uri"], self.test_metadata["nostr_uri"])
            self.assertEqual(posts[0]["links"], self.test_metadata["links"])
            self.assertEqual(posts[0]["uploaded_at"], self.test_metadata["uploaded_at"])

    def test_get_nostr_posts_with_additional_files(self):
        """Test getting Nostr posts with additional metadata files"""
        # Mock the filesystem functions
        with patch(
            "src.nosvid.platforms.nostr.get_platform_dir"
        ) as mock_get_dir, patch("os.path.exists", return_value=True), patch(
            "src.nosvid.platforms.nostr.load_json_file"
        ) as mock_load, patch(
            "os.listdir", return_value=["metadata.json", "additional_event_id.json"]
        ):
            # Set up the mock return values
            mock_get_dir.return_value = self.nostr_dir

            # Set up the mock load_json_file to return different values based on the file path
            def side_effect(file_path):
                if file_path.endswith("metadata.json"):
                    return self.test_metadata
                elif file_path.endswith("additional_event_id.json"):
                    return self.additional_metadata
                return {}

            mock_load.side_effect = side_effect

            # Test getting the posts
            posts = nostr.get_nostr_posts(self.video_dir)
            self.assertEqual(len(posts), 2)

            # Posts should be sorted by uploaded_at (newest first)
            self.assertEqual(posts[0]["event_id"], "additional_event_id")
            self.assertEqual(posts[1]["event_id"], self.test_metadata["event_id"])

    def test_get_nostr_posts_with_error(self):
        """Test getting Nostr posts with an error loading metadata"""
        # Mock the filesystem functions
        with patch(
            "src.nosvid.platforms.nostr.get_platform_dir"
        ) as mock_get_dir, patch("os.path.exists", return_value=True), patch(
            "src.nosvid.platforms.nostr.load_json_file"
        ) as mock_load, patch(
            "os.listdir", return_value=["metadata.json"]
        ):
            # Set up the mock return values
            mock_get_dir.return_value = self.nostr_dir
            mock_load.side_effect = Exception("Test exception")

            # Test getting the posts (should handle the error gracefully)
            posts = nostr.get_nostr_posts(self.video_dir)
            self.assertEqual(posts, [])

    def test_get_nostr_posts_with_additional_file_error(self):
        """Test getting Nostr posts with an error loading additional metadata"""
        # Mock the filesystem functions
        with patch(
            "src.nosvid.platforms.nostr.get_platform_dir"
        ) as mock_get_dir, patch("os.path.exists", return_value=True), patch(
            "src.nosvid.platforms.nostr.load_json_file"
        ) as mock_load, patch(
            "os.listdir", return_value=["metadata.json", "additional_event_id.json"]
        ):
            # Set up the mock return values
            mock_get_dir.return_value = self.nostr_dir

            # Set up the mock load_json_file to return different values based on the file path
            def side_effect(file_path):
                if file_path.endswith("metadata.json"):
                    return self.test_metadata
                elif file_path.endswith("additional_event_id.json"):
                    raise Exception("Test exception")
                return {}

            mock_load.side_effect = side_effect

            # Test getting the posts (should handle the error gracefully)
            posts = nostr.get_nostr_posts(self.video_dir)
            self.assertEqual(len(posts), 1)  # Should still get the valid post
            self.assertEqual(posts[0]["event_id"], self.test_metadata["event_id"])

    def test_post_video_to_nostr(self):
        """Test posting a video to Nostr"""
        # Mock the upload_to_nostr function
        with patch("src.nosvid.platforms.nostr.upload_to_nostr") as mock_upload:
            # Set up the mock return value
            mock_upload.return_value = {"event_id": "test_event_id"}

            # Call the function
            result = nostr.post_video_to_nostr(
                video_id="test_video_id",
                title="Test Video",
                description="Test Description",
                video_url="https://example.com/video",
                private_key="test_private_key",
                debug=True,
            )

            # Check the result
            self.assertEqual(result, {"event_id": "test_event_id"})

            # Check that upload_to_nostr was called with the correct arguments
            mock_upload.assert_called_once_with(
                video_id="test_video_id",
                title="Test Video",
                description="Test Description",
                video_url="https://example.com/video",
                private_key="test_private_key",
                debug=True,
            )


if __name__ == "__main__":
    unittest.main()

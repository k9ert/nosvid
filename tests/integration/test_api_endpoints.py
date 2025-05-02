"""
Test that the API endpoints are defined correctly
"""

import unittest
import inspect
from src.nosvid.api.app import app

class TestApiEndpoints(unittest.TestCase):
    """Test that the API endpoints are defined correctly"""

    def test_api_endpoints_exist(self):
        """Test that the API endpoints exist"""
        # Get all routes
        routes = app.routes

        # Check that the expected endpoints exist
        endpoint_paths = [route.path for route in routes]

        # Check for the videos endpoint
        self.assertIn("/videos", endpoint_paths)

        # Check for the video by ID endpoint
        self.assertIn("/videos/{video_id}", endpoint_paths)

        # Check for the download endpoints
        download_paths = [route.path for route in routes if route.path.endswith("/download")]
        # Check for the new YouTube download endpoint
        self.assertIn("/videos/{video_id}/platforms/youtube/download", download_paths)
        # The old endpoint should still exist (as deprecated)
        self.assertTrue(
            "/videos/{video_id}/download" in download_paths or
            any(route.path == "/videos/{video_id}/download" for route in routes),
            "The deprecated download endpoint should still exist"
        )

    def test_api_endpoint_methods(self):
        """Test that the API endpoints have the correct methods"""
        # Get all routes
        routes = app.routes

        # Check the methods for each endpoint
        for route in routes:
            if route.path == "/videos":
                self.assertEqual(route.methods, {"GET"})
            elif route.path == "/videos/{video_id}":
                self.assertEqual(route.methods, {"GET"})
            elif route.path == "/videos/{video_id}/platforms/youtube/download":
                self.assertEqual(route.methods, {"POST"})
            # The old endpoint should still be POST if it exists
            elif route.path == "/videos/{video_id}/download":
                self.assertEqual(route.methods, {"POST"})

if __name__ == "__main__":
    unittest.main()

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
        
        # Check for the download endpoint
        download_paths = [route.path for route in routes if route.path.endswith("/download")]
        self.assertIn("/videos/{video_id}/download", download_paths)
    
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
            elif route.path == "/videos/{video_id}/download":
                self.assertEqual(route.methods, {"POST"})

if __name__ == "__main__":
    unittest.main()

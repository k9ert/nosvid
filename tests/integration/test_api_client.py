"""
Integration test for the API using FastAPI's test client
"""

import unittest

from src.nosvid.api.app import app


class TestApiClient(unittest.TestCase):
    """Integration test for the API endpoints"""

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

        # Check for the video MP4 endpoint
        self.assertIn("/videos/{video_id}/mp4", endpoint_paths)

        # Check for the download endpoints
        download_paths = [
            route.path for route in routes if route.path.endswith("/download")
        ]
        # Check for the YouTube download endpoint
        self.assertIn("/videos/{video_id}/platforms/youtube/download", download_paths)
        # Check for the download status endpoint
        self.assertIn("/status/download", endpoint_paths)

    def test_nostr_post_serialization(self):
        """Test that NostrPost objects are properly serialized"""
        from src.nosvid.models.video import NostrPost, Video

        # Create a mock video with NostrPost objects
        video = Video(
            video_id="test123",
            title="Test Video",
            published_at="2023-01-01T12:00:00",
            duration=60,
        )

        # Add a NostrPost to the video
        post = NostrPost(
            event_id="test_event_id",
            pubkey="test_pubkey",
            uploaded_at="2023-01-01T12:00:00",
            nostr_uri="nostr:note1test",
            links={"test": "https://test.com"},
        )
        video.nostr_posts.append(post)

        # Convert the video to a dictionary using the same logic as in the API
        nostr_posts = [post.to_dict() for post in video.nostr_posts]

        # Create a copy of the video with nostr_posts as dictionaries
        video_dict = {
            "video_id": video.video_id,
            "title": video.title,
            "published_at": video.published_at,
            "duration": video.duration,
            "platforms": {
                name: platform.to_dict() for name, platform in video.platforms.items()
            },
            "nostr_posts": nostr_posts,
            "npubs": video.npubs,
            "synced_at": video.synced_at,
        }

        # Check that the NostrPost was properly serialized
        self.assertIn("nostr_posts", video_dict)
        self.assertEqual(len(video_dict["nostr_posts"]), 1)
        self.assertEqual(video_dict["nostr_posts"][0]["event_id"], "test_event_id")


if __name__ == "__main__":
    unittest.main()

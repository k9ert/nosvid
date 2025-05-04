"""
Tests for the Video model
"""

import unittest

from src.nosvid.models.video import NostrPost, Platform, Video


class TestPlatform(unittest.TestCase):
    """Tests for the Platform class"""

    def test_platform_creation(self):
        """Test creating a Platform"""
        platform = Platform(name="youtube", url="https://youtube.com/watch?v=123")

        self.assertEqual(platform.name, "youtube")
        self.assertEqual(platform.url, "https://youtube.com/watch?v=123")
        self.assertFalse(platform.downloaded)
        self.assertIsNone(platform.downloaded_at)
        self.assertFalse(platform.uploaded)
        self.assertIsNone(platform.uploaded_at)

    def test_platform_from_dict(self):
        """Test creating a Platform from a dictionary"""
        data = {
            "name": "youtube",
            "url": "https://youtube.com/watch?v=123",
            "downloaded": True,
            "downloaded_at": "2023-01-01T12:00:00",
            "uploaded": True,
            "uploaded_at": "2023-01-02T12:00:00",
        }

        platform = Platform.from_dict(data)

        self.assertEqual(platform.name, "youtube")
        self.assertEqual(platform.url, "https://youtube.com/watch?v=123")
        self.assertTrue(platform.downloaded)
        self.assertEqual(platform.downloaded_at, "2023-01-01T12:00:00")
        self.assertTrue(platform.uploaded)
        self.assertEqual(platform.uploaded_at, "2023-01-02T12:00:00")

    def test_platform_to_dict(self):
        """Test converting a Platform to a dictionary"""
        platform = Platform(
            name="youtube",
            url="https://youtube.com/watch?v=123",
            downloaded=True,
            downloaded_at="2023-01-01T12:00:00",
            uploaded=True,
            uploaded_at="2023-01-02T12:00:00",
        )

        data = platform.to_dict()

        self.assertEqual(data["name"], "youtube")
        self.assertEqual(data["url"], "https://youtube.com/watch?v=123")
        self.assertTrue(data["downloaded"])
        self.assertEqual(data["downloaded_at"], "2023-01-01T12:00:00")
        self.assertTrue(data["uploaded"])
        self.assertEqual(data["uploaded_at"], "2023-01-02T12:00:00")


class TestNostrPost(unittest.TestCase):
    """Tests for the NostrPost class"""

    def test_nostr_post_creation(self):
        """Test creating a NostrPost"""
        post = NostrPost(
            event_id="123", pubkey="abc", uploaded_at="2023-01-01T12:00:00"
        )

        self.assertEqual(post.event_id, "123")
        self.assertEqual(post.pubkey, "abc")
        self.assertEqual(post.uploaded_at, "2023-01-01T12:00:00")
        self.assertIsNone(post.nostr_uri)
        self.assertEqual(post.links, {})

    def test_nostr_post_from_dict(self):
        """Test creating a NostrPost from a dictionary"""
        data = {
            "event_id": "123",
            "pubkey": "abc",
            "uploaded_at": "2023-01-01T12:00:00",
            "nostr_uri": "nostr:123",
            "links": {"snort": "https://snort.social/e/123"},
        }

        post = NostrPost.from_dict(data)

        self.assertEqual(post.event_id, "123")
        self.assertEqual(post.pubkey, "abc")
        self.assertEqual(post.uploaded_at, "2023-01-01T12:00:00")
        self.assertEqual(post.nostr_uri, "nostr:123")
        self.assertEqual(post.links, {"snort": "https://snort.social/e/123"})

    def test_nostr_post_to_dict(self):
        """Test converting a NostrPost to a dictionary"""
        post = NostrPost(
            event_id="123",
            pubkey="abc",
            uploaded_at="2023-01-01T12:00:00",
            nostr_uri="nostr:123",
            links={"snort": "https://snort.social/e/123"},
        )

        data = post.to_dict()

        self.assertEqual(data["event_id"], "123")
        self.assertEqual(data["pubkey"], "abc")
        self.assertEqual(data["uploaded_at"], "2023-01-01T12:00:00")
        self.assertEqual(data["nostr_uri"], "nostr:123")
        self.assertEqual(data["links"], {"snort": "https://snort.social/e/123"})


class TestVideo(unittest.TestCase):
    """Tests for the Video class"""

    def test_video_creation(self):
        """Test creating a Video"""
        video = Video(
            video_id="123", title="Test Video", published_at="2023-01-01T12:00:00"
        )

        self.assertEqual(video.video_id, "123")
        self.assertEqual(video.title, "Test Video")
        self.assertEqual(video.published_at, "2023-01-01T12:00:00")
        self.assertEqual(video.duration, 0)
        self.assertEqual(video.platforms, {})
        self.assertEqual(video.nostr_posts, [])
        self.assertEqual(video.npubs, {})
        self.assertIsNone(video.synced_at)

    def test_video_from_dict(self):
        """Test creating a Video from a dictionary"""
        data = {
            "video_id": "123",
            "title": "Test Video",
            "published_at": "2023-01-01T12:00:00",
            "duration": 60,
            "platforms": {
                "youtube": {
                    "url": "https://youtube.com/watch?v=123",
                    "downloaded": True,
                    "downloaded_at": "2023-01-01T12:00:00",
                },
                "nostr": {
                    "posts": [
                        {
                            "event_id": "456",
                            "pubkey": "abc",
                            "uploaded_at": "2023-01-02T12:00:00",
                        }
                    ]
                },
            },
            "npubs": {"chat": ["npub1", "npub2"], "description": ["npub3"]},
            "synced_at": "2023-01-03T12:00:00",
        }

        video = Video.from_dict(data)

        self.assertEqual(video.video_id, "123")
        self.assertEqual(video.title, "Test Video")
        self.assertEqual(video.published_at, "2023-01-01T12:00:00")
        self.assertEqual(video.duration, 60)

        # Check platforms
        self.assertEqual(len(video.platforms), 2)
        self.assertIn("youtube", video.platforms)
        self.assertIn("nostr", video.platforms)

        youtube = video.platforms["youtube"]
        self.assertEqual(youtube.name, "youtube")
        self.assertEqual(youtube.url, "https://youtube.com/watch?v=123")
        self.assertTrue(youtube.downloaded)
        self.assertEqual(youtube.downloaded_at, "2023-01-01T12:00:00")

        # Check nostr posts
        self.assertEqual(len(video.nostr_posts), 1)
        post = video.nostr_posts[0]
        self.assertEqual(post.event_id, "456")
        self.assertEqual(post.pubkey, "abc")
        self.assertEqual(post.uploaded_at, "2023-01-02T12:00:00")

        # Check npubs
        self.assertEqual(
            video.npubs, {"chat": ["npub1", "npub2"], "description": ["npub3"]}
        )

        self.assertEqual(video.synced_at, "2023-01-03T12:00:00")

    def test_video_to_dict(self):
        """Test converting a Video to a dictionary"""
        # Create platforms
        youtube = Platform(
            name="youtube",
            url="https://youtube.com/watch?v=123",
            downloaded=True,
            downloaded_at="2023-01-01T12:00:00",
        )

        nostr = Platform(
            name="nostr", url="", uploaded=True, uploaded_at="2023-01-02T12:00:00"
        )

        # Create nostr post
        post = NostrPost(
            event_id="456", pubkey="abc", uploaded_at="2023-01-02T12:00:00"
        )

        # Create video
        video = Video(
            video_id="123",
            title="Test Video",
            published_at="2023-01-01T12:00:00",
            duration=60,
            platforms={"youtube": youtube, "nostr": nostr},
            nostr_posts=[post],
            npubs={"chat": ["npub1", "npub2"], "description": ["npub3"]},
            synced_at="2023-01-03T12:00:00",
        )

        # Convert to dict
        data = video.to_dict()

        self.assertEqual(data["video_id"], "123")
        self.assertEqual(data["title"], "Test Video")
        self.assertEqual(data["published_at"], "2023-01-01T12:00:00")
        self.assertEqual(data["duration"], 60)

        # Check platforms
        self.assertEqual(len(data["platforms"]), 2)
        self.assertIn("youtube", data["platforms"])
        self.assertIn("nostr", data["platforms"])

        youtube_data = data["platforms"]["youtube"]
        self.assertEqual(youtube_data["url"], "https://youtube.com/watch?v=123")
        self.assertTrue(youtube_data["downloaded"])
        self.assertEqual(youtube_data["downloaded_at"], "2023-01-01T12:00:00")

        # Check nostr posts
        self.assertIn("posts", data["platforms"]["nostr"])
        posts = data["platforms"]["nostr"]["posts"]
        self.assertEqual(len(posts), 1)
        post_data = posts[0]
        self.assertEqual(post_data["event_id"], "456")
        self.assertEqual(post_data["pubkey"], "abc")
        self.assertEqual(post_data["uploaded_at"], "2023-01-02T12:00:00")

        # Check npubs
        self.assertEqual(
            data["npubs"], {"chat": ["npub1", "npub2"], "description": ["npub3"]}
        )

        self.assertEqual(data["synced_at"], "2023-01-03T12:00:00")


if __name__ == "__main__":
    unittest.main()

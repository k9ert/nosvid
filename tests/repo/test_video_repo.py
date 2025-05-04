"""
Tests for the VideoRepo
"""

import os
import shutil
import tempfile
import unittest

from src.nosvid.models.video import Platform, Video
from src.nosvid.repo.video_repo import FileSystemVideoRepo


class TestFileSystemVideoRepo(unittest.TestCase):
    """Tests for the FileSystemVideoRepo"""

    def setUp(self):
        """Set up the test environment"""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.repo = FileSystemVideoRepo(self.temp_dir)
        self.channel_title = "TestChannel"

        # Create test videos
        self.video1 = Video(
            video_id="video1",
            title="Test Video 1",
            published_at="2023-01-01T12:00:00",
            duration=60,
        )

        self.video2 = Video(
            video_id="video2",
            title="Test Video 2",
            published_at="2023-01-02T12:00:00",
            duration=120,
        )

        self.video3 = Video(
            video_id="video3",
            title="Test Video 3",
            published_at="2023-01-03T12:00:00",
            duration=180,
        )

    def tearDown(self):
        """Clean up the test environment"""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_save_and_get_by_id(self):
        """Test saving a video and retrieving it by ID"""
        # Save the video
        result = self.repo.save(self.video1, self.channel_title)
        self.assertTrue(result)

        # Get the video by ID
        video = self.repo.get_by_id(self.video1.video_id, self.channel_title)

        # Check that the video was retrieved correctly
        self.assertIsNotNone(video)
        self.assertEqual(video.video_id, self.video1.video_id)
        self.assertEqual(video.title, self.video1.title)
        self.assertEqual(video.published_at, self.video1.published_at)
        self.assertEqual(video.duration, self.video1.duration)

    def test_get_by_id_not_found(self):
        """Test retrieving a video by ID that doesn't exist"""
        video = self.repo.get_by_id("nonexistent", self.channel_title)
        self.assertIsNone(video)

    def test_list_empty(self):
        """Test listing videos when there are none"""
        videos = self.repo.list(self.channel_title)
        self.assertEqual(len(videos), 0)

    def test_list_with_videos(self):
        """Test listing videos"""
        # Save some videos
        self.repo.save(self.video1, self.channel_title)
        self.repo.save(self.video2, self.channel_title)
        self.repo.save(self.video3, self.channel_title)

        # List all videos
        videos = self.repo.list(self.channel_title)

        # Check that all videos were retrieved
        self.assertEqual(len(videos), 3)

        # Check that videos are sorted by published_at in descending order by default
        self.assertEqual(videos[0].video_id, self.video3.video_id)
        self.assertEqual(videos[1].video_id, self.video2.video_id)
        self.assertEqual(videos[2].video_id, self.video1.video_id)

    def test_list_with_pagination(self):
        """Test listing videos with pagination"""
        # Save some videos
        self.repo.save(self.video1, self.channel_title)
        self.repo.save(self.video2, self.channel_title)
        self.repo.save(self.video3, self.channel_title)

        # List videos with limit
        videos = self.repo.list(self.channel_title, limit=2)

        # Check that only the specified number of videos were retrieved
        self.assertEqual(len(videos), 2)
        self.assertEqual(videos[0].video_id, self.video3.video_id)
        self.assertEqual(videos[1].video_id, self.video2.video_id)

        # List videos with offset
        videos = self.repo.list(self.channel_title, offset=1)

        # Check that videos were retrieved with the specified offset
        self.assertEqual(len(videos), 2)
        self.assertEqual(videos[0].video_id, self.video2.video_id)
        self.assertEqual(videos[1].video_id, self.video1.video_id)

        # List videos with limit and offset
        videos = self.repo.list(self.channel_title, limit=1, offset=1)

        # Check that videos were retrieved with the specified limit and offset
        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0].video_id, self.video2.video_id)

    def test_list_with_sorting(self):
        """Test listing videos with sorting"""
        # Save some videos
        self.repo.save(self.video1, self.channel_title)
        self.repo.save(self.video2, self.channel_title)
        self.repo.save(self.video3, self.channel_title)

        # List videos sorted by published_at in ascending order
        videos = self.repo.list(
            self.channel_title, sort_by="published_at", sort_order="asc"
        )

        # Check that videos are sorted correctly
        self.assertEqual(len(videos), 3)
        self.assertEqual(videos[0].video_id, self.video1.video_id)
        self.assertEqual(videos[1].video_id, self.video2.video_id)
        self.assertEqual(videos[2].video_id, self.video3.video_id)

        # List videos sorted by duration in descending order
        videos = self.repo.list(
            self.channel_title, sort_by="duration", sort_order="desc"
        )

        # Check that videos are sorted correctly
        self.assertEqual(len(videos), 3)
        self.assertEqual(videos[0].video_id, self.video3.video_id)
        self.assertEqual(videos[1].video_id, self.video2.video_id)
        self.assertEqual(videos[2].video_id, self.video1.video_id)

        # List videos sorted by title in ascending order
        videos = self.repo.list(self.channel_title, sort_by="title", sort_order="asc")

        # Check that videos are sorted correctly
        self.assertEqual(len(videos), 3)
        self.assertEqual(videos[0].video_id, self.video1.video_id)
        self.assertEqual(videos[1].video_id, self.video2.video_id)
        self.assertEqual(videos[2].video_id, self.video3.video_id)

    def test_delete(self):
        """Test deleting a video"""
        # Save a video
        self.repo.save(self.video1, self.channel_title)

        # Check that the video exists
        video = self.repo.get_by_id(self.video1.video_id, self.channel_title)
        self.assertIsNotNone(video)

        # Delete the video
        result = self.repo.delete(self.video1.video_id, self.channel_title)
        self.assertTrue(result)

        # Check that the video no longer exists
        video = self.repo.get_by_id(self.video1.video_id, self.channel_title)
        self.assertIsNone(video)

    def test_delete_not_found(self):
        """Test deleting a video that doesn't exist"""
        result = self.repo.delete("nonexistent", self.channel_title)
        self.assertFalse(result)

    def test_update(self):
        """Test updating a video"""
        # Save a video
        self.repo.save(self.video1, self.channel_title)

        # Get the video
        video = self.repo.get_by_id(self.video1.video_id, self.channel_title)

        # Update the video
        video.title = "Updated Title"
        video.duration = 90
        video.platforms["youtube"] = Platform(
            name="youtube",
            url="https://youtube.com/watch?v=video1",
            downloaded=True,
            downloaded_at="2023-01-01T12:00:00",
        )

        # Save the updated video
        result = self.repo.save(video, self.channel_title)
        self.assertTrue(result)

        # Get the updated video
        updated_video = self.repo.get_by_id(self.video1.video_id, self.channel_title)

        # Check that the video was updated correctly
        self.assertEqual(updated_video.title, "Updated Title")
        self.assertEqual(updated_video.duration, 90)
        self.assertIn("youtube", updated_video.platforms)
        self.assertEqual(
            updated_video.platforms["youtube"].url, "https://youtube.com/watch?v=video1"
        )
        self.assertTrue(updated_video.platforms["youtube"].downloaded)
        self.assertEqual(
            updated_video.platforms["youtube"].downloaded_at, "2023-01-01T12:00:00"
        )


if __name__ == "__main__":
    unittest.main()

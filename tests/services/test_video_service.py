"""
Tests for the VideoService
"""

import unittest
from unittest.mock import Mock, patch
from src.nosvid.models.video import Video, Platform
from src.nosvid.services.video_service import VideoService

class TestVideoService(unittest.TestCase):
    """Tests for the VideoService"""
    
    def setUp(self):
        """Set up the test environment"""
        self.mock_repo = Mock()
        self.service = VideoService(self.mock_repo)
        self.channel_title = "TestChannel"
        
        # Create test videos
        self.video1 = Video(
            video_id="video1",
            title="Test Video 1",
            published_at="2023-01-01T12:00:00",
            duration=60
        )
        
        self.video2 = Video(
            video_id="video2",
            title="Test Video 2",
            published_at="2023-01-02T12:00:00",
            duration=120
        )
        
        self.video3 = Video(
            video_id="video3",
            title="Test Video 3",
            published_at="2023-01-03T12:00:00",
            duration=180
        )
    
    def test_get_video_success(self):
        """Test getting a video successfully"""
        # Set up the mock
        self.mock_repo.get_by_id.return_value = self.video1
        
        # Call the service
        result = self.service.get_video("video1", self.channel_title)
        
        # Check the result
        self.assertTrue(result.success)
        self.assertEqual(result.data, self.video1)
        
        # Check that the repository was called correctly
        self.mock_repo.get_by_id.assert_called_once_with("video1", self.channel_title)
    
    def test_get_video_not_found(self):
        """Test getting a video that doesn't exist"""
        # Set up the mock
        self.mock_repo.get_by_id.return_value = None
        
        # Call the service
        result = self.service.get_video("nonexistent", self.channel_title)
        
        # Check the result
        self.assertTrue(result.success)
        self.assertIsNone(result.data)
        
        # Check that the repository was called correctly
        self.mock_repo.get_by_id.assert_called_once_with("nonexistent", self.channel_title)
    
    def test_get_video_error(self):
        """Test getting a video with an error"""
        # Set up the mock
        self.mock_repo.get_by_id.side_effect = Exception("Test error")
        
        # Call the service
        result = self.service.get_video("video1", self.channel_title)
        
        # Check the result
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Test error")
        
        # Check that the repository was called correctly
        self.mock_repo.get_by_id.assert_called_once_with("video1", self.channel_title)
    
    def test_list_videos_success(self):
        """Test listing videos successfully"""
        # Set up the mock
        self.mock_repo.list.return_value = [self.video1, self.video2, self.video3]
        
        # Call the service
        result = self.service.list_videos(self.channel_title)
        
        # Check the result
        self.assertTrue(result.success)
        self.assertEqual(result.data, [self.video1, self.video2, self.video3])
        
        # Check that the repository was called correctly
        self.mock_repo.list.assert_called_once_with(
            channel_title=self.channel_title,
            limit=None,
            offset=0,
            sort_by="published_at",
            sort_order="desc"
        )
    
    def test_list_videos_with_pagination(self):
        """Test listing videos with pagination"""
        # Set up the mock
        self.mock_repo.list.return_value = [self.video2, self.video3]
        
        # Call the service
        result = self.service.list_videos(
            self.channel_title,
            limit=2,
            offset=1
        )
        
        # Check the result
        self.assertTrue(result.success)
        self.assertEqual(result.data, [self.video2, self.video3])
        
        # Check that the repository was called correctly
        self.mock_repo.list.assert_called_once_with(
            channel_title=self.channel_title,
            limit=2,
            offset=1,
            sort_by="published_at",
            sort_order="desc"
        )
    
    def test_list_videos_with_sorting(self):
        """Test listing videos with sorting"""
        # Set up the mock
        self.mock_repo.list.return_value = [self.video1, self.video2, self.video3]
        
        # Call the service
        result = self.service.list_videos(
            self.channel_title,
            sort_by="title",
            sort_order="asc"
        )
        
        # Check the result
        self.assertTrue(result.success)
        self.assertEqual(result.data, [self.video1, self.video2, self.video3])
        
        # Check that the repository was called correctly
        self.mock_repo.list.assert_called_once_with(
            channel_title=self.channel_title,
            limit=None,
            offset=0,
            sort_by="title",
            sort_order="asc"
        )
    
    def test_list_videos_error(self):
        """Test listing videos with an error"""
        # Set up the mock
        self.mock_repo.list.side_effect = Exception("Test error")
        
        # Call the service
        result = self.service.list_videos(self.channel_title)
        
        # Check the result
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Test error")
        
        # Check that the repository was called correctly
        self.mock_repo.list.assert_called_once_with(
            channel_title=self.channel_title,
            limit=None,
            offset=0,
            sort_by="published_at",
            sort_order="desc"
        )
    
    @patch('src.nosvid.services.video_service.download_video_func')
    def test_download_video_success(self, mock_download):
        """Test downloading a video successfully"""
        # Set up the mocks
        self.mock_repo.get_by_id.return_value = self.video1
        self.mock_repo.save.return_value = True
        mock_download.return_value = {'success': True}
        
        # Call the service
        result = self.service.download_video("video1", self.channel_title)
        
        # Check the result
        self.assertTrue(result.success)
        self.assertTrue(result.data)
        
        # Check that the repository was called correctly
        self.mock_repo.get_by_id.assert_called_once_with("video1", self.channel_title)
        self.mock_repo.save.assert_called_once()
        
        # Check that the download function was called correctly
        mock_download.assert_called_once_with(
            video_id="video1",
            videos_dir=f"./repository/{self.channel_title}/videos",
            quality="best"
        )
        
        # Check that the video was updated correctly
        saved_video = self.mock_repo.save.call_args[0][0]
        self.assertIn("youtube", saved_video.platforms)
        self.assertTrue(saved_video.platforms["youtube"].downloaded)
        self.assertIsNotNone(saved_video.platforms["youtube"].downloaded_at)
    
    @patch('src.nosvid.services.video_service.download_video_func')
    def test_download_video_not_found(self, mock_download):
        """Test downloading a video that doesn't exist"""
        # Set up the mocks
        self.mock_repo.get_by_id.return_value = None
        
        # Call the service
        result = self.service.download_video("nonexistent", self.channel_title)
        
        # Check the result
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Video not found: nonexistent")
        
        # Check that the repository was called correctly
        self.mock_repo.get_by_id.assert_called_once_with("nonexistent", self.channel_title)
        
        # Check that the download function was not called
        mock_download.assert_not_called()
    
    @patch('src.nosvid.services.video_service.download_video_func')
    def test_download_video_download_error(self, mock_download):
        """Test downloading a video with a download error"""
        # Set up the mocks
        self.mock_repo.get_by_id.return_value = self.video1
        mock_download.return_value = {'success': False, 'error': 'Download error'}
        
        # Call the service
        result = self.service.download_video("video1", self.channel_title)
        
        # Check the result
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Failed to download video: Download error")
        
        # Check that the repository was called correctly
        self.mock_repo.get_by_id.assert_called_once_with("video1", self.channel_title)
        
        # Check that the download function was called correctly
        mock_download.assert_called_once_with(
            video_id="video1",
            videos_dir=f"./repository/{self.channel_title}/videos",
            quality="best"
        )
    
    @patch('src.nosvid.services.video_service.download_video_func')
    def test_download_video_save_error(self, mock_download):
        """Test downloading a video with a save error"""
        # Set up the mocks
        self.mock_repo.get_by_id.return_value = self.video1
        self.mock_repo.save.return_value = False
        mock_download.return_value = {'success': True}
        
        # Call the service
        result = self.service.download_video("video1", self.channel_title)
        
        # Check the result
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Failed to save video metadata")
        
        # Check that the repository was called correctly
        self.mock_repo.get_by_id.assert_called_once_with("video1", self.channel_title)
        self.mock_repo.save.assert_called_once()
        
        # Check that the download function was called correctly
        mock_download.assert_called_once_with(
            video_id="video1",
            videos_dir=f"./repository/{self.channel_title}/videos",
            quality="best"
        )
    
    def test_save_video_success(self):
        """Test saving a video successfully"""
        # Set up the mock
        self.mock_repo.save.return_value = True
        
        # Call the service
        result = self.service.save_video(self.video1, self.channel_title)
        
        # Check the result
        self.assertTrue(result.success)
        self.assertTrue(result.data)
        
        # Check that the repository was called correctly
        self.mock_repo.save.assert_called_once_with(self.video1, self.channel_title)
    
    def test_save_video_error(self):
        """Test saving a video with an error"""
        # Set up the mock
        self.mock_repo.save.return_value = False
        
        # Call the service
        result = self.service.save_video(self.video1, self.channel_title)
        
        # Check the result
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Failed to save video")
        
        # Check that the repository was called correctly
        self.mock_repo.save.assert_called_once_with(self.video1, self.channel_title)
    
    def test_delete_video_success(self):
        """Test deleting a video successfully"""
        # Set up the mock
        self.mock_repo.delete.return_value = True
        
        # Call the service
        result = self.service.delete_video("video1", self.channel_title)
        
        # Check the result
        self.assertTrue(result.success)
        self.assertTrue(result.data)
        
        # Check that the repository was called correctly
        self.mock_repo.delete.assert_called_once_with("video1", self.channel_title)
    
    def test_delete_video_error(self):
        """Test deleting a video with an error"""
        # Set up the mock
        self.mock_repo.delete.return_value = False
        
        # Call the service
        result = self.service.delete_video("video1", self.channel_title)
        
        # Check the result
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Failed to delete video: video1")
        
        # Check that the repository was called correctly
        self.mock_repo.delete.assert_called_once_with("video1", self.channel_title)

if __name__ == "__main__":
    unittest.main()

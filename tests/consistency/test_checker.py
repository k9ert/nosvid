"""
Tests for consistency checker functionality
"""

import os
import json
import shutil
import tempfile
import unittest
import logging
from unittest.mock import patch, MagicMock

from src.nosvid.consistency.checker import ConsistencyChecker


class TestConsistencyChecker(unittest.TestCase):
    """
    Test consistency checker functionality
    """

    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.videos_dir = os.path.join(self.temp_dir, 'videos')
        os.makedirs(self.videos_dir)

        # Set up logger
        self.logger = logging.getLogger('test_consistency_checker')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.NullHandler())

    def tearDown(self):
        """Clean up test environment"""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def _create_video_dir(self, video_id, metadata=None):
        """Create a video directory with metadata"""
        video_dir = os.path.join(self.videos_dir, video_id)
        os.makedirs(video_dir, exist_ok=True)

        if metadata:
            metadata_file = os.path.join(video_dir, 'metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)

        return video_dir

    def _create_platform_dir(self, video_dir, platform, metadata=None):
        """Create a platform directory with metadata"""
        platform_dir = os.path.join(video_dir, platform)
        os.makedirs(platform_dir, exist_ok=True)

        if metadata:
            metadata_file = os.path.join(platform_dir, 'metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)

        return platform_dir

    @patch('src.nosvid.consistency.checker.setup_directory_structure')
    def test_init(self, mock_setup):
        """Test initializing the consistency checker"""
        mock_setup.return_value = {'videos_dir': self.videos_dir}
        
        checker = ConsistencyChecker(self.temp_dir, 'Test Channel', self.logger)
        
        self.assertEqual(checker.output_dir, self.temp_dir)
        self.assertEqual(checker.channel_title, 'Test Channel')
        self.assertEqual(checker.logger, self.logger)
        self.assertEqual(checker.videos_dir, self.videos_dir)
        
        mock_setup.assert_called_once_with(self.temp_dir, 'Test Channel')

    @patch('src.nosvid.consistency.checker.setup_directory_structure')
    def test_check_empty_repository(self, mock_setup):
        """Test checking an empty repository"""
        mock_setup.return_value = {'videos_dir': self.videos_dir}
        
        checker = ConsistencyChecker(self.temp_dir, 'Test Channel', self.logger)
        result = checker.check()
        
        self.assertEqual(result['total'], 0)
        self.assertEqual(result['checked'], 0)
        self.assertEqual(result['inconsistencies'], 0)
        self.assertEqual(result['issues'], [])

    @patch('src.nosvid.consistency.checker.setup_directory_structure')
    @patch('src.nosvid.consistency.checker.generate_metadata_from_files')
    @patch('src.nosvid.consistency.checker.process_video_directory')
    def test_check_missing_metadata(self, mock_process, mock_generate, mock_setup):
        """Test checking a video with missing metadata"""
        mock_setup.return_value = {'videos_dir': self.videos_dir}
        mock_generate.return_value = {'title': 'Test Video', 'video_id': 'test123'}
        mock_process.return_value = ([], [])
        
        # Create a video directory without metadata
        self._create_video_dir('test123')
        
        checker = ConsistencyChecker(self.temp_dir, 'Test Channel', self.logger)
        result = checker.check()
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['checked'], 1)
        self.assertEqual(result['inconsistencies'], 1)
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['issues'][0]['video_id'], 'test123')
        self.assertEqual(result['issues'][0]['issue'], 'missing_metadata')
        self.assertEqual(result['issues'][0]['fixed'], False)

    @patch('src.nosvid.consistency.checker.setup_directory_structure')
    @patch('src.nosvid.consistency.checker.generate_metadata_from_files')
    @patch('src.nosvid.consistency.checker.process_video_directory')
    @patch('src.nosvid.consistency.checker.compare_metadata')
    def test_check_consistent_metadata(self, mock_compare, mock_process, mock_generate, mock_setup):
        """Test checking a video with consistent metadata"""
        mock_setup.return_value = {'videos_dir': self.videos_dir}
        mock_generate.return_value = {'title': 'Test Video', 'video_id': 'test123'}
        mock_process.return_value = ([], [])
        mock_compare.return_value = []  # No differences
        
        # Create a video directory with metadata
        self._create_video_dir('test123', {'title': 'Test Video', 'video_id': 'test123'})
        
        checker = ConsistencyChecker(self.temp_dir, 'Test Channel', self.logger)
        result = checker.check()
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['checked'], 1)
        self.assertEqual(result['inconsistencies'], 0)
        self.assertEqual(result['issues'], [])

    @patch('src.nosvid.consistency.checker.setup_directory_structure')
    @patch('src.nosvid.consistency.checker.generate_metadata_from_files')
    @patch('src.nosvid.consistency.checker.process_video_directory')
    @patch('src.nosvid.consistency.checker.compare_metadata')
    def test_check_inconsistent_metadata(self, mock_compare, mock_process, mock_generate, mock_setup):
        """Test checking a video with inconsistent metadata"""
        mock_setup.return_value = {'videos_dir': self.videos_dir}
        mock_generate.return_value = {'title': 'Updated Title', 'video_id': 'test123'}
        mock_process.return_value = ([], [])
        mock_compare.return_value = ['Different title']  # Differences found
        
        # Create a video directory with metadata
        self._create_video_dir('test123', {'title': 'Test Video', 'video_id': 'test123'})
        
        checker = ConsistencyChecker(self.temp_dir, 'Test Channel', self.logger)
        result = checker.check()
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['checked'], 1)
        self.assertEqual(result['inconsistencies'], 1)
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['issues'][0]['video_id'], 'test123')
        self.assertEqual(result['issues'][0]['issue'], 'inconsistent_metadata')
        self.assertEqual(result['issues'][0]['differences'], ['Different title'])
        self.assertEqual(result['issues'][0]['fixed'], False)

    @patch('src.nosvid.consistency.checker.setup_directory_structure')
    @patch('src.nosvid.consistency.checker.generate_metadata_from_files')
    @patch('src.nosvid.consistency.checker.process_video_directory')
    @patch('src.nosvid.consistency.checker.compare_metadata')
    @patch('src.nosvid.consistency.checker.save_json_file')
    def test_check_fix_inconsistent_metadata(self, mock_save, mock_compare, mock_process, mock_generate, mock_setup):
        """Test checking and fixing a video with inconsistent metadata"""
        mock_setup.return_value = {'videos_dir': self.videos_dir}
        mock_generate.return_value = {'title': 'Updated Title', 'video_id': 'test123'}
        mock_process.return_value = ([], [])
        mock_compare.return_value = ['Different title']  # Differences found
        
        # Create a video directory with metadata
        self._create_video_dir('test123', {'title': 'Test Video', 'video_id': 'test123'})
        
        checker = ConsistencyChecker(self.temp_dir, 'Test Channel', self.logger)
        result = checker.check(fix_issues=True)
        
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['checked'], 1)
        self.assertEqual(result['inconsistencies'], 1)
        self.assertEqual(len(result['issues']), 1)
        self.assertEqual(result['issues'][0]['video_id'], 'test123')
        self.assertEqual(result['issues'][0]['issue'], 'inconsistent_metadata')
        self.assertEqual(result['issues'][0]['differences'], ['Different title'])
        self.assertEqual(result['issues'][0]['fixed'], True)
        
        # Verify that save_json_file was called
        mock_save.assert_called_once()


if __name__ == '__main__':
    unittest.main()

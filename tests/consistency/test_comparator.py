"""
Tests for metadata comparison functionality
"""

import unittest
from datetime import datetime

from src.nosvid.consistency.comparator import (
    compare_metadata,
    _compare_basic_fields,
    _compare_platforms,
    _compare_youtube_platform,
    _compare_nostrmedia_platform,
    _compare_npubs
)


class TestComparator(unittest.TestCase):
    """
    Test metadata comparison functionality
    """

    def test_compare_metadata_identical(self):
        """Test comparing identical metadata"""
        metadata = {
            'title': 'Test Video',
            'video_id': 'test123',
            'published_at': '2023-01-01T00:00:00Z',
            'duration': 60,
            'platforms': {
                'youtube': {
                    'url': 'https://www.youtube.com/watch?v=test123',
                    'downloaded': True
                },
                'nostrmedia': {
                    'url': 'https://nostrmedia.com/test123'
                }
            },
            'npubs': {
                'chat': ['npub1', 'npub2'],
                'description': ['npub3']
            }
        }
        differences = compare_metadata(metadata, metadata)
        self.assertEqual(differences, [])

    def test_compare_metadata_different_title(self):
        """Test comparing metadata with different title"""
        metadata1 = {
            'title': 'Test Video 1',
            'video_id': 'test123'
        }
        metadata2 = {
            'title': 'Test Video 2',
            'video_id': 'test123'
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, ['Different title'])

    def test_compare_metadata_different_published_at(self):
        """Test comparing metadata with different published_at"""
        metadata1 = {
            'title': 'Test Video',
            'published_at': '2023-01-01T00:00:00Z'
        }
        metadata2 = {
            'title': 'Test Video',
            'published_at': '2023-02-01T00:00:00Z'
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, ['Different published_at'])

    def test_compare_metadata_normalized_published_at(self):
        """Test comparing metadata with different but normalized published_at"""
        metadata1 = {
            'title': 'Test Video',
            'published_at': '2023-01-01T00:00:00Z'
        }
        metadata2 = {
            'title': 'Test Video',
            'published_at': '2023-01-01'  # Will be normalized to 2023-01-01T00:00:00Z
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, [])

    def test_compare_metadata_missing_platforms(self):
        """Test comparing metadata with missing platforms section"""
        metadata1 = {
            'title': 'Test Video',
            'platforms': {
                'youtube': {
                    'url': 'https://www.youtube.com/watch?v=test123'
                }
            }
        }
        metadata2 = {
            'title': 'Test Video'
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, [])  # No differences because fresh doesn't have platforms

        differences = compare_metadata(metadata2, metadata1)
        self.assertEqual(differences, ['Missing platforms section'])

    def test_compare_metadata_different_youtube_url(self):
        """Test comparing metadata with different YouTube URL"""
        metadata1 = {
            'platforms': {
                'youtube': {
                    'url': 'https://www.youtube.com/watch?v=test123'
                }
            }
        }
        metadata2 = {
            'platforms': {
                'youtube': {
                    'url': 'https://www.youtube.com/watch?v=test456'
                }
            }
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, ['Different YouTube URL'])

    def test_compare_metadata_different_youtube_download_status(self):
        """Test comparing metadata with different YouTube download status"""
        metadata1 = {
            'platforms': {
                'youtube': {
                    'downloaded': True
                }
            }
        }
        metadata2 = {
            'platforms': {
                'youtube': {
                    'downloaded': False
                }
            }
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, ['Different YouTube download status'])

    def test_compare_metadata_different_nostrmedia_url(self):
        """Test comparing metadata with different nostrmedia URL"""
        metadata1 = {
            'platforms': {
                'nostrmedia': {
                    'url': 'https://nostrmedia.com/test123'
                }
            }
        }
        metadata2 = {
            'platforms': {
                'nostrmedia': {
                    'url': 'https://nostrmedia.com/test456'
                }
            }
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, ['Different nostrmedia URL'])

    def test_compare_metadata_missing_npubs(self):
        """Test comparing metadata with missing npubs section"""
        metadata1 = {
            'title': 'Test Video',
            'npubs': {
                'chat': ['npub1', 'npub2']
            }
        }
        metadata2 = {
            'title': 'Test Video'
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, [])  # No differences because fresh doesn't have npubs

        differences = compare_metadata(metadata2, metadata1)
        self.assertEqual(differences, [])  # No differences because we don't check for extra npubs in existing

    def test_compare_metadata_different_chat_npubs(self):
        """Test comparing metadata with different chat npubs"""
        metadata1 = {
            'npubs': {
                'chat': ['npub1', 'npub2']
            }
        }
        metadata2 = {
            'npubs': {
                'chat': ['npub1', 'npub3']
            }
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, ['Different chat npubs'])

    def test_compare_metadata_different_description_npubs(self):
        """Test comparing metadata with different description npubs"""
        metadata1 = {
            'npubs': {
                'description': ['npub1', 'npub2']
            }
        }
        metadata2 = {
            'npubs': {
                'description': ['npub1', 'npub3']
            }
        }
        differences = compare_metadata(metadata1, metadata2)
        self.assertEqual(differences, ['Different description npubs'])


if __name__ == '__main__':
    unittest.main()

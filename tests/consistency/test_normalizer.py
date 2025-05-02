"""
Tests for date normalization functionality
"""

import unittest
from datetime import datetime

from src.nosvid.consistency.normalizer import normalize_date, normalize_metadata_dates


class TestNormalizer(unittest.TestCase):
    """
    Test date normalization functionality
    """

    def test_normalize_date_empty(self):
        """Test normalizing an empty date string"""
        self.assertEqual(normalize_date(""), "")
        self.assertEqual(normalize_date(None), "")

    def test_normalize_date_iso8601_with_z(self):
        """Test normalizing an ISO 8601 date with Z"""
        date_str = "2023-01-01T12:34:56Z"
        self.assertEqual(normalize_date(date_str), date_str)

    def test_normalize_date_iso8601_with_microseconds(self):
        """Test normalizing an ISO 8601 date with microseconds"""
        date_str = "2023-01-01T12:34:56.789Z"
        expected = "2023-01-01T12:34:56Z"
        self.assertEqual(normalize_date(date_str), expected)

    def test_normalize_date_iso8601_without_z(self):
        """Test normalizing an ISO 8601 date without Z"""
        date_str = "2023-01-01T12:34:56"
        expected = "2023-01-01T12:34:56Z"
        self.assertEqual(normalize_date(date_str), expected)

    def test_normalize_date_standard_datetime(self):
        """Test normalizing a standard datetime string"""
        date_str = "2023-01-01 12:34:56"
        expected = "2023-01-01T12:34:56Z"
        self.assertEqual(normalize_date(date_str), expected)

    def test_normalize_date_just_date(self):
        """Test normalizing a date-only string"""
        date_str = "2023-01-01"
        expected = "2023-01-01T00:00:00Z"
        self.assertEqual(normalize_date(date_str), expected)

    def test_normalize_date_yyyymmdd(self):
        """Test normalizing a YYYYMMDD string"""
        date_str = "20230101"
        expected = "2023-01-01T00:00:00Z"
        self.assertEqual(normalize_date(date_str), expected)

    def test_normalize_date_invalid(self):
        """Test normalizing an invalid date string"""
        date_str = "not-a-date"
        self.assertEqual(normalize_date(date_str), date_str)

    def test_normalize_metadata_dates_empty(self):
        """Test normalizing dates in an empty metadata dictionary"""
        metadata = {}
        self.assertEqual(normalize_metadata_dates(metadata), {})

    def test_normalize_metadata_dates_none(self):
        """Test normalizing dates in a None metadata"""
        self.assertEqual(normalize_metadata_dates(None), None)

    def test_normalize_metadata_dates_published_at(self):
        """Test normalizing published_at in metadata"""
        metadata = {
            'title': 'Test Video',
            'published_at': '2023-01-01'
        }
        expected = {
            'title': 'Test Video',
            'published_at': '2023-01-01T00:00:00Z'
        }
        self.assertEqual(normalize_metadata_dates(metadata), expected)

    def test_normalize_metadata_dates_platforms(self):
        """Test normalizing dates in platforms section"""
        metadata = {
            'title': 'Test Video',
            'published_at': '2023-01-01',
            'platforms': {
                'youtube': {
                    'downloaded_at': '2023-02-01'
                },
                'nostrmedia': {
                    'uploaded_at': '2023-03-01'
                },
                'nostr': {
                    'posts': [
                        {
                            'event_id': 'event1',
                            'uploaded_at': '2023-04-01'
                        },
                        {
                            'event_id': 'event2',
                            'uploaded_at': '2023-05-01'
                        }
                    ]
                }
            }
        }
        expected = {
            'title': 'Test Video',
            'published_at': '2023-01-01T00:00:00Z',
            'platforms': {
                'youtube': {
                    'downloaded_at': '2023-02-01T00:00:00Z'
                },
                'nostrmedia': {
                    'uploaded_at': '2023-03-01T00:00:00Z'
                },
                'nostr': {
                    'posts': [
                        {
                            'event_id': 'event1',
                            'uploaded_at': '2023-04-01T00:00:00Z'
                        },
                        {
                            'event_id': 'event2',
                            'uploaded_at': '2023-05-01T00:00:00Z'
                        }
                    ]
                }
            }
        }
        self.assertEqual(normalize_metadata_dates(metadata), expected)


if __name__ == '__main__':
    unittest.main()

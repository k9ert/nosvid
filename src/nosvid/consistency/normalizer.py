"""
Date normalization utilities for consistency checking
"""

from datetime import datetime
from typing import List, Optional


def normalize_date(date_str: str) -> str:
    """
    Normalize date format to ISO 8601 (YYYY-MM-DDThh:mm:ssZ)

    Args:
        date_str: Date string to normalize

    Returns:
        Normalized date string
    """
    if not date_str:
        return ""

    # List of possible formats to try
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",       # ISO 8601 with Z
        "%Y-%m-%dT%H:%M:%S.%fZ",    # ISO 8601 with microseconds and Z
        "%Y-%m-%dT%H:%M:%S",        # ISO 8601 without Z
        "%Y-%m-%dT%H:%M:%S.%f",     # ISO 8601 with microseconds without Z
        "%Y-%m-%d %H:%M:%S",        # Standard datetime
        "%Y-%m-%d",                 # Just date
        "%Y%m%d",                   # YYYYMMDD
    ]

    # Try each format
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Return in standard ISO format
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    # If all formats fail, return the original string
    return date_str


def normalize_metadata_dates(metadata: dict) -> dict:
    """
    Normalize all date fields in metadata

    Args:
        metadata: Metadata dictionary

    Returns:
        Metadata with normalized dates
    """
    if not metadata:
        return metadata

    # Create a copy to avoid modifying the original
    normalized = metadata.copy()

    # Normalize published_at
    if 'published_at' in normalized and normalized['published_at']:
        normalized['published_at'] = normalize_date(normalized['published_at'])

    # Normalize platform-specific dates
    if 'platforms' in normalized:
        platforms = normalized['platforms']

        # YouTube dates
        if 'youtube' in platforms and 'downloaded_at' in platforms['youtube']:
            platforms['youtube']['downloaded_at'] = normalize_date(platforms['youtube']['downloaded_at'])

        # Nostrmedia dates
        if 'nostrmedia' in platforms and 'uploaded_at' in platforms['nostrmedia']:
            platforms['nostrmedia']['uploaded_at'] = normalize_date(platforms['nostrmedia']['uploaded_at'])

        # Nostr dates
        if 'nostr' in platforms and 'posts' in platforms['nostr']:
            for post in platforms['nostr']['posts']:
                if 'uploaded_at' in post:
                    post['uploaded_at'] = normalize_date(post['uploaded_at'])

    return normalized

"""
YouTube API utilities for nosvid
"""

import os
import json
import time
from datetime import datetime, timedelta
import googleapiclient.discovery

def build_youtube_api(api_key):
    """
    Build YouTube API client

    Args:
        api_key: YouTube API key

    Returns:
        YouTube API client
    """
    return googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

def get_channel_info(api_key, channel_id):
    """
    Get channel information using the YouTube API

    Args:
        api_key: YouTube API key
        channel_id: ID of the channel

    Returns:
        Dictionary with channel information
    """
    youtube = build_youtube_api(api_key)

    request = youtube.channels().list(
        part="snippet",
        id=channel_id
    )
    response = request.execute()

    if response.get('items'):
        channel_info = response['items'][0]['snippet']
        return {
            'title': channel_info.get('title', 'Unknown Channel'),
            'description': channel_info.get('description', ''),
            'published_at': channel_info.get('publishedAt', ''),
            'thumbnail_url': channel_info.get('thumbnails', {}).get('high', {}).get('url', '')
        }

    return {
        'title': 'Unknown Channel',
        'description': '',
        'published_at': '',
        'thumbnail_url': ''
    }

def get_cached_videos(metadata_dir, channel_id, max_age_hours=24):
    """
    Get cached videos for a channel if available and not too old

    Args:
        metadata_dir: Directory containing metadata
        channel_id: ID of the channel
        max_age_hours: Maximum age of cache in hours

    Returns:
        Tuple of (videos, cache_exists, cache_fresh)
        - videos: List of video dictionaries (empty if no cache)
        - cache_exists: Boolean indicating if cache exists
        - cache_fresh: Boolean indicating if cache is fresh
    """
    cache_file = os.path.join(metadata_dir, f"channel_videos_{channel_id}.json")

    if not os.path.exists(cache_file):
        return [], False, False

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        # Check if cache is fresh
        cache_time = datetime.fromisoformat(cache_data.get('timestamp', '2000-01-01T00:00:00'))
        current_time = datetime.now()
        max_age = timedelta(hours=max_age_hours)

        cache_fresh = (current_time - cache_time) < max_age

        if not cache_fresh:
            print(f"Cache is older than {max_age_hours} hours. Will refresh from API.")
        else:
            print(f"Using cached video list from {cache_time.isoformat()}")

        return cache_data.get('videos', []), True, cache_fresh
    except Exception as e:
        print(f"Error reading cache: {e}")
        return [], False, False

def save_videos_to_cache(metadata_dir, channel_id, videos):
    """
    Save videos to cache

    Args:
        metadata_dir: Directory containing metadata
        channel_id: ID of the channel
        videos: List of video dictionaries
    """
    cache_file = os.path.join(metadata_dir, f"channel_videos_{channel_id}.json")

    cache_data = {
        'channel_id': channel_id,
        'timestamp': datetime.now().isoformat(),
        'video_count': len(videos),
        'videos': videos
    }

    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(videos)} videos to cache")
    except Exception as e:
        print(f"Error saving cache: {e}")

def get_all_videos_from_channel(api_key, channel_id, metadata_dir=None, force_refresh=False, max_pages=None):
    """
    Get all videos from a channel

    Args:
        api_key: YouTube API key
        channel_id: ID of the channel
        metadata_dir: Directory to store/read cache (if None, no caching)
        force_refresh: Force refresh from API even if cache is fresh
        max_pages: Maximum number of pages to fetch (None for all)

    Returns:
        List of video dictionaries
    """
    # Try to use cache if available
    if metadata_dir and not force_refresh:
        videos, cache_exists, cache_fresh = get_cached_videos(metadata_dir, channel_id)
        if cache_exists and cache_fresh:
            return videos

    # If no cache or cache is stale, fetch from API
    youtube = build_youtube_api(api_key)

    videos = []
    next_page_token = None
    page_count = 0

    # First, try to get videos using search API
    while True:
        page_count += 1
        if max_pages and page_count > max_pages:
            print(f"Reached maximum number of pages ({max_pages}). Stopping.")
            break

        try:
            request = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=50,  # Maximum allowed by API
                order="date",  # Sort by date (newest first)
                type="video",  # Only return videos (not playlists or channels)
                pageToken=next_page_token
            )
            response = request.execute()

            # Process each video
            for item in response['items']:
                video = {
                    'title': item['snippet']['title'],
                    'video_id': item['id']['videoId'],
                    'published_at': item['snippet']['publishedAt'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                }
                videos.append(video)

            # Check if there are more pages
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                print(f"No more pages available. Retrieved all videos.")
                break

            print(f"Fetched {len(videos)} videos so far (page {page_count})...")

        except Exception as e:
            print(f"Error fetching videos: {e}")
            # If we hit an API quota limit or other error, return what we have so far
            break

    print(f"Total videos fetched: {len(videos)} from {page_count} pages")

    # Save to cache if metadata_dir is provided
    if metadata_dir:
        save_videos_to_cache(metadata_dir, channel_id, videos)

    return videos

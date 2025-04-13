"""
YouTube API utilities for nosvid
"""

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

def get_all_videos_from_channel(api_key, channel_id, max_pages=None):
    """
    Get all videos from a channel
    
    Args:
        api_key: YouTube API key
        channel_id: ID of the channel
        max_pages: Maximum number of pages to fetch (None for all)
        
    Returns:
        List of video dictionaries
    """
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
    return videos

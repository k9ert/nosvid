"""
Listing functionality for nosvid
"""

import os
from ..utils.filesystem import load_json_file, get_video_dir

def list_videos(videos_dir, show_downloaded=True, show_not_downloaded=True):
    """
    List all videos in the repository
    
    Args:
        videos_dir: Directory containing videos
        show_downloaded: Whether to show downloaded videos
        show_not_downloaded: Whether to show videos that have not been downloaded
        
    Returns:
        List of video dictionaries
    """
    if not os.path.exists(videos_dir):
        print(f"Videos directory not found: {videos_dir}")
        return []
    
    videos = []
    
    for video_id in os.listdir(videos_dir):
        video_dir = get_video_dir(videos_dir, video_id)
        
        if not os.path.isdir(video_dir):
            continue
        
        metadata_file = os.path.join(video_dir, 'metadata.json')
        
        if not os.path.exists(metadata_file):
            continue
        
        metadata = load_json_file(metadata_file)
        
        # Filter based on download status
        if metadata.get('downloaded') and not show_downloaded:
            continue
        
        if not metadata.get('downloaded') and not show_not_downloaded:
            continue
        
        videos.append({
            'video_id': video_id,
            'title': metadata.get('title', 'Unknown'),
            'published_at': metadata.get('published_at', ''),
            'downloaded': metadata.get('downloaded', False),
            'url': metadata.get('url', '')
        })
    
    # Sort by published date (newest first)
    videos.sort(key=lambda x: x.get('published_at', ''), reverse=True)
    
    return videos

def print_video_list(videos, show_index=True):
    """
    Print a list of videos
    
    Args:
        videos: List of video dictionaries
        show_index: Whether to show the index number
    """
    if not videos:
        print("No videos found.")
        return
    
    print(f"\nFound {len(videos)} videos:")
    print("-" * 80)
    
    for i, video in enumerate(videos, 1):
        status = "✓" if video['downloaded'] else " "
        
        if show_index:
            print(f"{i:3d}. [{status}] {video['video_id']} - {video['title']} ({video['published_at']})")
        else:
            print(f"[{status}] {video['video_id']} - {video['title']} ({video['published_at']})")
    
    print("-" * 80)

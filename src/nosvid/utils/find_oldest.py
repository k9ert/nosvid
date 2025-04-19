"""
Utility functions for finding the oldest video that meets a specific condition
"""

from typing import Dict, Any, Optional, Callable

from ..metadata.list import list_videos
from ..utils.filesystem import get_video_dir


def find_oldest_video(videos_dir: str, condition: Callable[[Dict[str, Any]], bool]) -> Optional[Dict[str, Any]]:
    """
    Find the oldest video that meets a specific condition

    Args:
        videos_dir: Directory containing videos
        condition: Function that takes a video dictionary and returns True if the video meets the condition

    Returns:
        The oldest video that meets the condition, or None if no video meets the condition
    """
    # Get all videos
    videos, _ = list_videos(videos_dir)

    # Filter videos that meet the condition
    filtered_videos = [video for video in videos if condition(video)]

    # Return the oldest video (videos are already sorted by published date, oldest first)
    return filtered_videos[0] if filtered_videos else None


def find_oldest_not_downloaded(videos_dir: str) -> Optional[Dict[str, Any]]:
    """
    Find the oldest video that hasn't been downloaded yet

    Args:
        videos_dir: Directory containing videos

    Returns:
        The oldest video that hasn't been downloaded yet, or None if all videos have been downloaded
    """
    return find_oldest_video(videos_dir, lambda video: not video['downloaded'])


def find_oldest_not_posted(videos_dir: str) -> Optional[Dict[str, Any]]:
    """
    Find the oldest video that hasn't been posted to Nostr yet

    Args:
        videos_dir: Directory containing videos

    Returns:
        The oldest video that hasn't been posted to Nostr yet, or None if all videos have been posted
    """
    def not_posted(video: Dict[str, Any]) -> bool:
        # Check if the video has been downloaded
        if not video['downloaded']:
            return False

        # Check if the video has been posted to Nostr
        has_nostr = False
        if 'platforms' in video and 'nostr' in video.get('platforms', {}):
            # Check if there are any posts in the nostr platform
            nostr_data = video['platforms']['nostr']
            if 'posts' in nostr_data and len(nostr_data['posts']) > 0:
                has_nostr = True
            # For backward compatibility with old metadata format
            elif 'event_id' in nostr_data:
                has_nostr = True

        # Return True if the video has been downloaded but not posted to Nostr
        # We don't require nostrmedia URL since the nostr command will handle that automatically
        return video['downloaded'] and not has_nostr

    return find_oldest_video(videos_dir, not_posted)


def find_oldest_video_without_download(channel_id: str) -> Optional[str]:
    """
    Find the oldest video that hasn't been downloaded yet

    Args:
        channel_id: Channel ID

    Returns:
        The video ID of the oldest video that hasn't been downloaded yet, or None if all videos have been downloaded
    """
    videos_dir = get_video_dir(channel_id)
    video = find_oldest_not_downloaded(videos_dir)
    return video['video_id'] if video else None


def find_oldest_video_without_nostr_post(channel_id: str) -> Optional[str]:
    """
    Find the oldest video that hasn't been posted to Nostr yet

    Args:
        channel_id: Channel ID

    Returns:
        The video ID of the oldest video that hasn't been posted to Nostr yet, or None if all videos have been posted
    """
    videos_dir = get_video_dir(channel_id)
    video = find_oldest_not_posted(videos_dir)
    return video['video_id'] if video else None


def find_oldest_not_uploaded_to_nostrmedia(videos_dir: str) -> Optional[Dict[str, Any]]:
    """
    Find the oldest video that hasn't been uploaded to nostrmedia yet

    Args:
        videos_dir: Directory containing videos

    Returns:
        The oldest video that hasn't been uploaded to nostrmedia yet, or None if all videos have been uploaded
    """
    def not_uploaded_to_nostrmedia(video: Dict[str, Any]) -> bool:
        # Check if the video has been downloaded
        if not video['downloaded']:
            return False

        # Check if the video has been uploaded to nostrmedia
        has_nostrmedia = False
        if 'platforms' in video and 'nostrmedia' in video.get('platforms', {}):
            # Check if there is a URL in the nostrmedia platform
            nostrmedia_data = video['platforms']['nostrmedia']
            if 'url' in nostrmedia_data and nostrmedia_data['url']:
                has_nostrmedia = True

        # Return True if the video has been downloaded but not uploaded to nostrmedia
        return video['downloaded'] and not has_nostrmedia

    return find_oldest_video(videos_dir, not_uploaded_to_nostrmedia)


def find_oldest_video_without_nostrmedia(channel_id: str) -> Optional[str]:
    """
    Find the oldest video that hasn't been uploaded to nostrmedia yet

    Args:
        channel_id: Channel ID

    Returns:
        The video ID of the oldest video that hasn't been uploaded to nostrmedia yet, or None if all videos have been uploaded
    """
    videos_dir = get_video_dir(channel_id)
    video = find_oldest_not_uploaded_to_nostrmedia(videos_dir)
    return video['video_id'] if video else None

"""
Video service for nosvid
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import threading
import os
import json

from ..models.video import Video, Platform
from ..models.result import Result
from ..repo.video_repo import VideoRepo
from ..download.video import download_video as download_video_func

# Global download lock to prevent concurrent downloads
download_lock = threading.Lock()

# Global download status
download_status = {
    "in_progress": False,
    "video_id": None,
    "started_at": None,
    "user": None
}

class VideoService:
    """
    Service for video operations
    """

    def __init__(self, video_repository: VideoRepo):
        """
        Initialize the service

        Args:
            video_repository: Repository for video operations
        """
        self.video_repository = video_repository

    def get_video(self, video_id: str, channel_title: str) -> Result[Optional[Video]]:
        """
        Get a video by ID

        Args:
            video_id: ID of the video
            channel_title: Title of the channel

        Returns:
            Result containing the Video object or None if not found
        """
        try:
            video = self.video_repository.get_by_id(video_id, channel_title)
            return Result.success(video)
        except Exception as e:
            return Result.failure(str(e))

    def list_videos(self,
                    channel_title: str,
                    limit: Optional[int] = None,
                    offset: Optional[int] = 0,
                    sort_by: str = "published_at",
                    sort_order: str = "desc") -> Result[List[Video]]:
        """
        List videos with pagination and sorting

        Args:
            channel_title: Title of the channel
            limit: Maximum number of videos to return
            offset: Number of videos to skip
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Result containing a list of Video objects
        """
        try:
            videos = self.video_repository.list(
                channel_title=channel_title,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order
            )
            return Result.success(videos)
        except Exception as e:
            return Result.failure(str(e))

    def download_video(self, video_id: str, channel_title: str, quality: str = "best", user: str = "anonymous") -> Result[bool]:
        """
        Download a video

        Args:
            video_id: ID of the video
            channel_title: Title of the channel
            quality: Quality of the video to download
            user: Identifier for the user initiating the download

        Returns:
            Result indicating success or failure
        """
        # Check if a download is already in progress
        if not download_lock.acquire(blocking=False):
            return Result.failure(f"Another download is already in progress for video {download_status['video_id']}. Please wait and try again.")

        try:
            # Update download status
            download_status["in_progress"] = True
            download_status["video_id"] = video_id
            download_status["started_at"] = datetime.now().isoformat()
            download_status["user"] = user

            # Get the video
            video_result = self.get_video(video_id, channel_title)
            if not video_result.success:
                return Result.failure(f"Failed to get video: {video_result.error}")

            video = video_result.data
            if not video:
                return Result.failure(f"Video not found: {video_id}")

            # Download the video
            download_result = download_video_func(
                video_id=video_id,
                videos_dir=f"./repository/{channel_title}/videos",
                quality=quality
            )

            if not download_result:
                return Result.failure(f"Failed to download video: Unknown error")

            # Update the video metadata
            if 'platforms' not in video.to_dict():
                video.platforms = {}

            if 'youtube' not in video.platforms:
                video.platforms['youtube'] = Platform(
                    name="youtube",
                    url=f"https://youtube.com/watch?v={video_id}"
                )

            video.platforms['youtube'].downloaded = True
            video.platforms['youtube'].downloaded_at = datetime.now().isoformat()

            # Save the updated video
            save_result = self.video_repository.save(video, channel_title)
            if not save_result:
                return Result.failure("Failed to save video metadata")

            return Result.success(True)
        except Exception as e:
            return Result.failure(str(e))
        finally:
            # Always reset download status and release the lock when done
            download_status["in_progress"] = False
            download_status["video_id"] = None
            download_status["started_at"] = None
            download_status["user"] = None
            download_lock.release()

    def get_cache_statistics(self, channel_title: str) -> Result[Dict[str, Any]]:
        """
        Get statistics about the video cache and repository

        Args:
            channel_title: Title of the channel

        Returns:
            Result containing statistics dictionary
        """
        try:
            # Get the base directory from the repository
            base_dir = self.video_repository.base_dir

            # Set up paths
            channel_dir = os.path.join(base_dir, channel_title)
            metadata_dir = os.path.join(channel_dir, 'metadata')
            videos_dir = os.path.join(channel_dir, 'videos')

            # Initialize statistics
            stats = {
                'total_in_cache': 0,
                'total_with_metadata': 0,
                'total_downloaded': 0,
                'total_uploaded_nm': 0,
                'total_posted_nostr': 0,
                'total_with_npubs': 0,
                'total_npubs': 0
            }

            # Get the channel ID (hardcoded for now)
            channel_id = "UCxSRxq14XIoMbFDEjMOPU5Q"  # Einundzwanzig Podcast

            # Check if cache file exists
            cache_file = os.path.join(metadata_dir, f"channel_videos_{channel_id}.json")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    stats['total_in_cache'] = cache_data.get('video_count', 0)
                except Exception as e:
                    print(f"Error reading cache: {e}")

            # Get list of videos with metadata
            videos = self.video_repository.list(channel_title)
            stats['total_with_metadata'] = len(videos)

            # Count downloaded, uploaded, and posted videos
            for video in videos:
                # Check if downloaded
                if video.platforms and 'youtube' in video.platforms and video.platforms['youtube'].downloaded:
                    stats['total_downloaded'] += 1

                # Check if uploaded to Nostrmedia
                if video.platforms and 'nostrmedia' in video.platforms and video.platforms['nostrmedia'].url:
                    stats['total_uploaded_nm'] += 1

                # Check if posted to Nostr
                if video.nostr_posts and len(video.nostr_posts) > 0:
                    stats['total_posted_nostr'] += 1

                # Count npubs
                if video.npubs:
                    npub_count = 0
                    if 'chat' in video.npubs:
                        npub_count += len(video.npubs['chat'])
                    if 'description' in video.npubs:
                        npub_count += len(video.npubs['description'])

                    if npub_count > 0:
                        stats['total_with_npubs'] += 1
                        stats['total_npubs'] += npub_count

            return Result.success(stats)
        except Exception as e:
            return Result.failure(str(e))

    def save_video(self, video: Video, channel_title: str) -> Result[bool]:
        """
        Save a video

        Args:
            video: Video object to save
            channel_title: Title of the channel

        Returns:
            Result indicating success or failure
        """
        try:
            result = self.video_repository.save(video, channel_title)
            if result:
                return Result.success(True)
            else:
                return Result.failure("Failed to save video")
        except Exception as e:
            return Result.failure(str(e))

    def delete_video(self, video_id: str, channel_title: str) -> Result[bool]:
        """
        Delete a video

        Args:
            video_id: ID of the video
            channel_title: Title of the channel

        Returns:
            Result indicating success or failure
        """
        try:
            result = self.video_repository.delete(video_id, channel_title)
            if result:
                return Result.success(True)
            else:
                return Result.failure(f"Failed to delete video: {video_id}")
        except Exception as e:
            return Result.failure(str(e))

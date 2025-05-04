"""
Video repository for nosvid
"""

import glob
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..models.video import Video
from ..utils.filesystem import (
    get_video_dir,
    load_json_file,
    save_json_file,
    setup_directory_structure,
)


class VideoRepo(ABC):
    """
    Abstract base class for video repositories
    """

    @abstractmethod
    def get_by_id(self, video_id: str, channel_title: str) -> Optional[Video]:
        """
        Get a video by ID

        Args:
            video_id: ID of the video
            channel_title: Title of the channel

        Returns:
            Video object or None if not found
        """
        pass

    @abstractmethod
    def list(
        self,
        channel_title: str,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        sort_by: str = "published_at",
        sort_order: str = "desc",
    ) -> List[Video]:
        """
        List videos with pagination and sorting

        Args:
            channel_title: Title of the channel
            limit: Maximum number of videos to return
            offset: Number of videos to skip
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            List of Video objects
        """
        pass

    @abstractmethod
    def save(self, video: Video, channel_title: str) -> bool:
        """
        Save a video

        Args:
            video: Video object to save
            channel_title: Title of the channel

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def delete(self, video_id: str, channel_title: str) -> bool:
        """
        Delete a video

        Args:
            video_id: ID of the video
            channel_title: Title of the channel

        Returns:
            True if successful, False otherwise
        """
        pass


class FileSystemVideoRepo(VideoRepo):
    """
    File system implementation of VideoRepo
    """

    def __init__(self, base_dir: str):
        """
        Initialize the repository

        Args:
            base_dir: Base directory for videos
        """
        self.base_dir = base_dir

    def get_by_id(self, video_id: str, channel_title: str) -> Optional[Video]:
        """
        Get a video by ID

        Args:
            video_id: ID of the video
            channel_title: Title of the channel

        Returns:
            Video object or None if not found
        """
        dirs = setup_directory_structure(self.base_dir, channel_title)
        video_dir = get_video_dir(dirs["videos_dir"], video_id)
        metadata_dir = dirs["metadata_dir"]

        # First check if the video directory exists and has metadata
        if os.path.exists(video_dir):
            metadata_file = os.path.join(video_dir, "metadata.json")
            if os.path.exists(metadata_file):
                metadata = load_json_file(metadata_file)
                return Video.from_dict(metadata)

        # If not found in the video directory, check the channel metadata files
        channel_metadata_files = glob.glob(
            os.path.join(metadata_dir, "channel_videos_*.json")
        )
        for channel_file in channel_metadata_files:
            try:
                channel_data = load_json_file(channel_file)
                if "videos" in channel_data:
                    for video_data in channel_data["videos"]:
                        if video_data.get("video_id") == video_id:
                            # Create a minimal Video object from channel metadata
                            return Video(
                                video_id=video_id,
                                title=video_data.get("title", ""),
                                published_at=video_data.get("published_at", ""),
                                duration=video_data.get("duration", 0),
                                platforms={},
                                nostr_posts=[],
                                npubs={},
                            )
            except Exception as e:
                print(f"Error reading channel metadata file {channel_file}: {e}")
                continue

        return None

    def list(
        self,
        channel_title: str,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        sort_by: str = "published_at",
        sort_order: str = "desc",
    ) -> List[Video]:
        """
        List videos with pagination and sorting

        Args:
            channel_title: Title of the channel
            limit: Maximum number of videos to return
            offset: Number of videos to skip
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            List of Video objects
        """
        dirs = setup_directory_structure(self.base_dir, channel_title)
        videos_dir = dirs["videos_dir"]

        # Check if the videos directory exists
        if not os.path.exists(videos_dir):
            return []

        # Get all video directories
        video_dirs = [
            d
            for d in os.listdir(videos_dir)
            if os.path.isdir(os.path.join(videos_dir, d))
        ]

        # Load metadata for each video
        videos = []
        for video_id in video_dirs:
            video = self.get_by_id(video_id, channel_title)
            if video:
                videos.append(video)

        # Sort videos
        reverse = sort_order.lower() == "desc"
        if sort_by == "published_at":
            videos.sort(key=lambda v: v.published_at, reverse=reverse)
        elif sort_by == "title":
            videos.sort(key=lambda v: v.title, reverse=reverse)
        elif sort_by == "duration":
            videos.sort(key=lambda v: v.duration, reverse=reverse)

        # Apply pagination
        if offset is not None and offset > 0:
            videos = videos[offset:]

        if limit is not None and limit > 0:
            videos = videos[:limit]

        return videos

    def save(self, video: Video, channel_title: str) -> bool:
        """
        Save a video

        Args:
            video: Video object to save
            channel_title: Title of the channel

        Returns:
            True if successful, False otherwise
        """
        try:
            dirs = setup_directory_structure(self.base_dir, channel_title)
            video_dir = get_video_dir(dirs["videos_dir"], video.video_id)

            # Create the video directory if it doesn't exist
            os.makedirs(video_dir, exist_ok=True)

            # Save metadata
            metadata_file = os.path.join(video_dir, "metadata.json")
            save_json_file(metadata_file, video.to_dict())

            return True
        except Exception as e:
            print(f"Error saving video: {e}")
            return False

    def delete(self, video_id: str, channel_title: str) -> bool:
        """
        Delete a video

        Args:
            video_id: ID of the video
            channel_title: Title of the channel

        Returns:
            True if successful, False otherwise
        """
        try:
            dirs = setup_directory_structure(self.base_dir, channel_title)
            video_dir = get_video_dir(dirs["videos_dir"], video_id)

            # Check if the video directory exists
            if not os.path.exists(video_dir):
                return False

            # Delete the video directory
            import shutil

            shutil.rmtree(video_dir)

            return True
        except Exception as e:
            print(f"Error deleting video: {e}")
            return False

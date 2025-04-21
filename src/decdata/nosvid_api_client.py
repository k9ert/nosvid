#!/usr/bin/env python3
"""
NosVid API Client for DecData

This module provides a client for interacting with the NosVid API.
It allows the DecData node to query the NosVid API for video information.
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any, Union


class NosVidAPIClient:
    """
    Client for interacting with the NosVid API.
    """

    def __init__(self, api_url: str = "http://localhost:2121/api"):
        """
        Initialize the NosVid API client.

        Args:
            api_url: URL of the NosVid API
        """
        self.api_url = api_url.rstrip('/')

    def list_videos(self,
                   limit: Optional[int] = None,
                   offset: int = 0,
                   sort_by: str = "published_at",
                   sort_order: str = "desc") -> Dict[str, Any]:
        """
        List videos from the NosVid API.

        Args:
            limit: Maximum number of videos to return
            offset: Number of videos to skip
            sort_by: Field to sort by
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            Dictionary containing video list and metadata
        """
        params = {
            'offset': offset,
            'sort_by': sort_by,
            'sort_order': sort_order
        }

        if limit is not None:
            params['limit'] = limit

        try:
            response = requests.get(f"{self.api_url}/videos", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing videos: {e}")
            return {'videos': [], 'total': 0, 'offset': offset, 'limit': limit}

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a video by ID from the NosVid API.

        Args:
            video_id: ID of the video

        Returns:
            Dictionary containing video information, or None if not found
        """
        try:
            response = requests.get(f"{self.api_url}/videos/{video_id}")
            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting video {video_id}: {e}")
            return None

    def download_video(self, video_id: str, quality: str = "best") -> bool:
        """
        Request the NosVid API to download a video from YouTube.

        Args:
            video_id: ID of the video
            quality: Quality of the video to download

        Returns:
            True if the download request was successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/videos/{video_id}/platforms/youtube/download",
                json={'quality': quality}
            )
            response.raise_for_status()
            return response.json().get('success', False)
        except requests.exceptions.RequestException as e:
            print(f"Error downloading video {video_id}: {e}")
            return False

    def upload_to_nostrmedia(self, video_id: str, private_key: str = None, debug: bool = False) -> bool:
        """
        Request the NosVid API to upload a video to nostrmedia.com.

        Args:
            video_id: ID of the video
            private_key: Private key string (hex or nsec format)
            debug: Whether to print debug information

        Returns:
            True if the upload request was successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/videos/{video_id}/platforms/nostrmedia/upload",
                json={
                    'private_key': private_key,
                    'debug': debug
                }
            )
            response.raise_for_status()
            return response.json().get('success', False)
        except requests.exceptions.RequestException as e:
            print(f"Error uploading video {video_id} to nostrmedia: {e}")
            return False

    def set_nostrmedia_url(self, video_id: str, url: str, hash_value: str = None, uploaded_at: str = None) -> bool:
        """
        Set an existing nostrmedia URL for a video.

        Args:
            video_id: ID of the video
            url: Nostrmedia URL
            hash_value: Hash of the video file (optional)
            uploaded_at: When the video was uploaded (optional)

        Returns:
            True if the request was successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/videos/{video_id}/platforms/nostrmedia",
                json={
                    'url': url,
                    'hash': hash_value,
                    'uploaded_at': uploaded_at
                }
            )
            response.raise_for_status()
            return response.json().get('success', False)
        except requests.exceptions.RequestException as e:
            print(f"Error setting nostrmedia URL for video {video_id}: {e}")
            return False

    def get_download_status(self) -> Dict[str, Any]:
        """
        Get the current download status from the NosVid API.

        Returns:
            Dictionary containing download status information
        """
        try:
            response = requests.get(f"{self.api_url}/download/status")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting download status: {e}")
            return {
                'in_progress': False,
                'video_id': None,
                'started_at': None,
                'user': None
            }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get repository statistics from the NosVid API.

        Returns:
            Dictionary containing statistics
        """
        try:
            response = requests.get(f"{self.api_url}/statistics")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting statistics: {e}")
            return {
                'total_in_cache': 0,
                'total_with_metadata': 0,
                'total_downloaded': 0,
                'total_uploaded_nm': 0,
                'total_posted_nostr': 0,
                'total_with_npubs': 0,
                'total_npubs': 0
            }

    def get_video_file_path(self, video_id: str, channel_title: str, base_dir: str = "./repository") -> Optional[str]:
        """
        Get the file path for a video based on the NosVid repository structure.

        Args:
            video_id: ID of the video
            channel_title: Title of the channel
            base_dir: Base directory for the repository

        Returns:
            Path to the video file, or None if not found
        """
        # This follows the NosVid repository structure
        video_dir = os.path.join(base_dir, channel_title, "videos", video_id, "youtube")

        # Look for MP4 files in the directory
        if os.path.exists(video_dir):
            for filename in os.listdir(video_dir):
                if filename.endswith('.mp4'):
                    return os.path.join(video_dir, filename)

        return None

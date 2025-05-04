#!/usr/bin/env python3
"""
NosVid API Client for DecData

This module provides a client for interacting with the NosVid API.
It allows the DecData node to query the NosVid API for video information.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Union

import requests


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
        self.api_url = api_url.rstrip("/")

    def list_videos(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        sort_by: str = "published_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
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
        params = {"offset": offset, "sort_by": sort_by, "sort_order": sort_order}

        if limit is not None:
            params["limit"] = limit

        try:
            response = requests.get(f"{self.api_url}/videos", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing videos: {e}")
            return {"videos": [], "total": 0, "offset": offset, "limit": limit}

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
                json={"quality": quality},
            )
            response.raise_for_status()
            return response.json().get("success", False)
        except requests.exceptions.RequestException as e:
            print(f"Error downloading video {video_id}: {e}")
            return False

    def upload_to_nostrmedia(
        self, video_id: str, private_key: str = None, debug: bool = False
    ) -> bool:
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
                json={"private_key": private_key, "debug": debug},
            )
            response.raise_for_status()
            return response.json().get("success", False)
        except requests.exceptions.RequestException as e:
            print(f"Error uploading video {video_id} to nostrmedia: {e}")
            return False

    def set_nostrmedia_url(
        self, video_id: str, url: str, hash_value: str = None, uploaded_at: str = None
    ) -> bool:
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
                json={"url": url, "hash": hash_value, "uploaded_at": uploaded_at},
            )
            response.raise_for_status()
            return response.json().get("success", False)
        except requests.exceptions.RequestException as e:
            print(f"Error setting nostrmedia URL for video {video_id}: {e}")
            return False

    def create_youtube_platform(
        self,
        video_id: str,
        url: str,
        data: Dict[str, Any],
        downloaded: bool = True,
        downloaded_at: str = None,
    ) -> bool:
        """
        Create YouTube platform data for a video.

        Args:
            video_id: ID of the video
            url: YouTube URL for the video
            data: Dictionary containing YouTube platform data
            downloaded: Whether the video has been downloaded
            downloaded_at: When the video was downloaded (ISO format)

        Returns:
            True if the request was successful, False otherwise
        """
        try:
            platform_data = {
                "url": url,
                "downloaded": downloaded,
                "downloaded_at": downloaded_at,
                "data": data,
            }

            response = requests.post(
                f"{self.api_url}/videos/{video_id}/platforms/youtube",
                json=platform_data,
            )
            response.raise_for_status()
            return response.json().get("success", False)
        except requests.exceptions.RequestException as e:
            print(f"Error creating YouTube platform data for video {video_id}: {e}")
            return False

    def update_metadata(self, video_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a video.

        Args:
            video_id: ID of the video
            metadata: Dictionary containing metadata to update

        Returns:
            True if the request was successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/videos/{video_id}/update-metadata", json=metadata
            )
            response.raise_for_status()
            return response.json().get("success", False)
        except requests.exceptions.RequestException as e:
            print(f"Error updating metadata for video {video_id}: {e}")
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
                "in_progress": False,
                "video_id": None,
                "started_at": None,
                "user": None,
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
                "total_in_cache": 0,
                "total_with_metadata": 0,
                "total_downloaded": 0,
                "total_uploaded_nm": 0,
                "total_posted_nostr": 0,
                "total_with_npubs": 0,
                "total_npubs": 0,
            }

    def get_video_file_content(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the video file content from the NosVid API.

        Args:
            video_id: ID of the video

        Returns:
            Dictionary containing file content and metadata, or None if not found
        """
        try:
            # First check if the video exists and is downloaded
            video_info = self.get_video(video_id)
            if not video_info:
                print(f"Video {video_id} not found")
                return None

            platforms = video_info.get("platforms", {})
            youtube = platforms.get("youtube", {})

            if not youtube.get("downloaded", False):
                print(f"Video {video_id} is not downloaded")
                return None

            # Get the video file content
            response = requests.get(f"{self.api_url}/videos/{video_id}/file")
            if response.status_code == 404:
                print(f"Video file for {video_id} not found")
                return None

            response.raise_for_status()

            # Get the file content
            file_data = response.content

            # Calculate file hash and size
            file_hash = hashlib.sha256(file_data).hexdigest()
            file_size = len(file_data)

            return {
                "video_id": video_id,
                "file_data": file_data,
                "file_hash": file_hash,
                "file_size": file_size,
                "title": video_info.get("title", ""),
                "published_at": video_info.get("published_at", ""),
                "duration": video_info.get("duration", 0),
                "platforms": platforms,
            }

        except requests.exceptions.RequestException as e:
            print(f"Error getting video file content for {video_id}: {e}")
            return None

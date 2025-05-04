#!/usr/bin/env python3
"""
Catalog Manager for DecData - Manages video catalogs

This module provides functionality for managing video catalogs in the DecData project.
"""

import json
import time
import threading
from typing import Dict, List, Any, Optional


class CatalogManager:
    """
    Catalog Manager for DecData.

    This class manages the video catalog and synchronization with the NosVid API.
    """

    def __init__(self, node, sync_interval: int = 300):
        """
        Initialize the Catalog Manager.

        Args:
            node: The DecData node this manager is associated with
            sync_interval: Interval in seconds for syncing with NosVid API
        """
        self.node = node
        self.sync_interval = sync_interval
        self.sync_thread = None
        self.sync_stop_event = threading.Event()

    def start(self):
        """
        Start the catalog manager and sync thread.
        """
        # Load the initial catalog
        self.load_local_catalog()

        # Start the sync thread
        self.sync_stop_event.clear()
        self.sync_thread = threading.Thread(target=self.sync_with_nosvid)
        self.sync_thread.daemon = True
        self.sync_thread.start()

    def stop(self):
        """
        Stop the catalog manager and sync thread.
        """
        # Stop the sync thread
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_stop_event.set()
            self.sync_thread.join(timeout=5)

    def load_local_catalog(self):
        """
        Load the local video catalog from the NosVid API.
        Uses pagination to fetch all videos.
        """
        try:
            # Initialize variables for pagination
            offset = 0
            batch_size = 100
            total_videos = 0
            all_videos = []

            print("Loading videos from NosVid API (this may take a while)...")

            # Fetch all videos using pagination
            while True:
                # Get a batch of videos from NosVid API
                response = self.node.nosvid_api.list_videos(limit=batch_size, offset=offset)
                videos_batch = response.get('videos', [])
                total_count = response.get('total', 0)

                if not videos_batch:
                    break

                # Add this batch to our collection
                all_videos.extend(videos_batch)
                total_videos += len(videos_batch)

                # Print progress
                print(f"Loaded {total_videos}/{total_count} videos...")

                # If we've fetched all videos, break
                if total_videos >= total_count or len(videos_batch) < batch_size:
                    break

                # Move to the next batch
                offset += batch_size

            # Update local catalog with downloaded videos
            for video in all_videos:
                video_id = video.get('video_id')
                if video_id:
                    # Check if the video has been downloaded
                    platforms = video.get('platforms', {})
                    youtube = platforms.get('youtube', {})

                    if youtube.get('downloaded', False):
                        # Add to catalog without file path (we'll fetch content on demand)
                        self.node.video_catalog[video_id] = {
                            'video_id': video_id,
                            'title': video.get('title', ''),
                            'published_at': video.get('published_at', ''),
                            'duration': video.get('duration', 0),
                            'platforms': platforms
                        }

            print(f"Loaded {len(self.node.video_catalog)} downloaded videos out of {total_videos} total videos from NosVid API")

        except Exception as e:
            print(f"Error loading videos from NosVid API: {e}")

    def sync_with_nosvid(self):
        """
        Periodically sync with the NosVid API.
        Uses pagination to fetch all videos.
        """
        while not self.sync_stop_event.is_set():
            try:
                print("Syncing with NosVid API...")

                # Initialize variables for pagination
                offset = 0
                batch_size = 100
                total_videos = 0
                all_videos = []

                # Fetch all videos using pagination
                while True:
                    # Check if we should stop
                    if self.sync_stop_event.is_set():
                        return

                    # Get a batch of videos from NosVid API
                    response = self.node.nosvid_api.list_videos(limit=batch_size, offset=offset)
                    videos_batch = response.get('videos', [])
                    total_count = response.get('total', 0)

                    if not videos_batch:
                        break

                    # Add this batch to our collection
                    all_videos.extend(videos_batch)
                    total_videos += len(videos_batch)

                    # Print progress
                    print(f"Syncing {total_videos}/{total_count} videos...")

                    # If we've fetched all videos, break
                    if total_videos >= total_count or len(videos_batch) < batch_size:
                        break

                    # Move to the next batch
                    offset += batch_size

                # Update local catalog with downloaded videos
                downloaded_count = 0
                for video in all_videos:
                    video_id = video.get('video_id')
                    if video_id:
                        # Check if the video has been downloaded
                        platforms = video.get('platforms', {})
                        youtube = platforms.get('youtube', {})

                        if youtube.get('downloaded', False):
                            # Add to catalog without file path (we'll fetch content on demand)
                            self.node.video_catalog[video_id] = {
                                'video_id': video_id,
                                'title': video.get('title', ''),
                                'published_at': video.get('published_at', ''),
                                'duration': video.get('duration', 0),
                                'platforms': platforms
                            }
                            downloaded_count += 1

                print(f"Synced {total_videos} videos from NosVid API, {downloaded_count} downloaded videos in local catalog")

                # Sleep until next sync
                for _ in range(self.sync_interval):
                    if self.sync_stop_event.is_set():
                        break
                    time.sleep(1)

            except Exception as e:
                print(f"Error syncing with NosVid API: {e}")
                # Sleep for a shorter time before retrying
                for _ in range(60):
                    if self.sync_stop_event.is_set():
                        break
                    time.sleep(1)

    def send_catalog_to_node(self, node):
        """
        Send the local video catalog to a node.

        Args:
            node: The node to send the catalog to
        """
        catalog_message = {
            'type': 'catalog',
            'node_id': self.node.id,
            'videos': list(self.node.video_catalog.keys())
        }

        try:
            self.node.send_to_node(node, json.dumps(catalog_message))
            print(f"Sent catalog to node {node.id} ({len(self.node.video_catalog)} videos)")

            # If we already have the other node's catalog, calculate which videos we have that they don't have
            if node.id in self.node.peers_catalog:
                our_videos = set(self.node.video_catalog.keys())
                their_videos = set(self.node.peers_catalog[node.id])
                videos_we_have_they_dont = our_videos - their_videos

                if videos_we_have_they_dont:
                    print(f"We have {len(videos_we_have_they_dont)} videos that node {node.id} doesn't have:")
                    for video_id in sorted(list(videos_we_have_they_dont)):
                        print(f"  - {video_id}")
                else:
                    print(f"We don't have any videos that node {node.id} doesn't have")
        except Exception as e:
            print(f"Error sending catalog to node {node.id}: {e}")

    def handle_catalog_message(self, node, message):
        """
        Handle a catalog message from another node.

        Args:
            node: The node that sent the message
            message: The catalog message
        """
        node_id = message.get('node_id')
        videos = message.get('videos', [])

        self.node.peers_catalog[node_id] = videos
        print(f"Received catalog from node {node_id} ({len(videos)} videos)")

        # Calculate which videos the other node has that we don't have
        our_videos = set(self.node.video_catalog.keys())
        their_videos = set(videos)
        videos_they_have_we_dont = their_videos - our_videos

        if videos_they_have_we_dont:
            print(f"Node {node_id} has {len(videos_they_have_we_dont)} videos that we don't have:")

            # For each video they have that we don't, request video_info
            for video_id in sorted(list(videos_they_have_we_dont)):
                print(f"  - {video_id}")

                # Request video info for this video
                from .message_handlers import request_video_info
                request_video_info(self.node, node, video_id)
        else:
            print(f"Node {node_id} doesn't have any videos that we don't have")

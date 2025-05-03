#!/usr/bin/env python3
"""
DecData Node - A peer-to-peer node for exchanging video data

This module implements a peer-to-peer node for the DecData project,
which enables decentralized exchange of video data collected by the NosVid project.
It extends the Node class from the p2pnetwork package.
"""

import json
import time
import hashlib
import threading
from typing import Dict, List, Optional, Any
from p2pnetwork.node import Node

from .nosvid_api_client import NosVidAPIClient


class DecDataNode(Node):
    """
    DecData Node for peer-to-peer video data exchange.

    This class extends the Node class from p2pnetwork to implement
    the specific functionality needed for the DecData project.
    """

    def __init__(self, host: str, port: int,
                 nosvid_api_url: str = "http://localhost:2121/api",
                 id: str = None, max_connections: int = 0,
                 sync_interval: int = 300):
        """
        Initialize the DecData node.

        Args:
            host: The host name or ip address to bind to
            port: The port number to bind to
            nosvid_api_url: URL of the NosVid API
            id: Node ID (optional, will be generated if not provided)
            max_connections: Maximum number of connections (0 for unlimited)
            sync_interval: Interval in seconds for syncing with NosVid API
        """
        super(DecDataNode, self).__init__(host, port, id, None, max_connections)

        # NosVid API client
        self.nosvid_api = NosVidAPIClient(nosvid_api_url)

        # Video catalog - maps video_id to metadata
        self.video_catalog: Dict[str, Dict[str, Any]] = {}

        # Peers catalog - maps node_id to available videos
        self.peers_catalog: Dict[str, List[str]] = {}

        # Active transfers
        self.active_transfers: Dict[str, Dict[str, Any]] = {}

        # Sync interval
        self.sync_interval = sync_interval

        # Sync thread
        self.sync_thread = None
        self.sync_stop_event = threading.Event()

        # Message handlers
        self.message_handlers = []

        # Load local video catalog
        self.load_local_catalog()

        print(f"DecDataNode: Started on {host}:{port}")

    def outbound_node_connected(self, node):
        """
        Event triggered when connected to another node.

        Args:
            node: The node that we connected to
        """
        print(f"Connected to node: {node.id}")
        self.send_catalog_to_node(node)

    def inbound_node_connected(self, node):
        """
        Event triggered when another node connects to this node.

        Args:
            node: The node that connected to us
        """
        print(f"Node connected: {node.id}")
        self.send_catalog_to_node(node)

    def inbound_node_disconnected(self, node):
        """
        Event triggered when a node disconnects from this node.

        Args:
            node: The node that disconnected
        """
        print(f"Node disconnected: {node.id}")
        if node.id in self.peers_catalog:
            del self.peers_catalog[node.id]

    def outbound_node_disconnected(self, node):
        """
        Event triggered when disconnected from another node.

        Args:
            node: The node we disconnected from
        """
        print(f"Disconnected from node: {node.id}")
        if node.id in self.peers_catalog:
            del self.peers_catalog[node.id]

    def start(self):
        """
        Start the node and the sync thread.
        """
        super(DecDataNode, self).start()

        # Start the sync thread
        self.sync_stop_event.clear()
        self.sync_thread = threading.Thread(target=self.sync_with_nosvid)
        self.sync_thread.daemon = True
        self.sync_thread.start()

    def stop(self):
        """
        Stop the node and the sync thread.
        """
        # Stop the sync thread
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_stop_event.set()
            self.sync_thread.join(timeout=5)

        super(DecDataNode, self).stop()

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
                    response = self.nosvid_api.list_videos(limit=batch_size, offset=offset)
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
                            self.video_catalog[video_id] = {
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

    def add_message_handler(self, handler):
        """
        Add a message handler function.

        The handler function should have the signature:
        handler(node, peer, data)

        Args:
            handler: The handler function to add
        """
        if handler not in self.message_handlers:
            self.message_handlers.append(handler)
            print(f"Added message handler: {handler.__name__ if hasattr(handler, '__name__') else handler}")

    def node_message(self, node, data):
        """
        Event triggered when a message is received from a node.

        Args:
            node: The node that sent the message
            data: The message data
        """
        # Safely print the message preview
        try:
            if isinstance(data, str):
                preview = data[:100]
            elif isinstance(data, dict):
                preview = str(data)[:100]
            else:
                preview = str(data)[:100]
            print(f"Message from node {node.id}: {preview}...")
        except Exception as e:
            print(f"Message from node {node.id}: <error displaying message preview: {e}>")

        # Call all registered message handlers
        for handler in self.message_handlers:
            try:
                handler(self, node, data)
            except Exception as e:
                print(f"Error in message handler {handler.__name__ if hasattr(handler, '__name__') else handler}: {e}")

        try:
            # Handle different data types
            if isinstance(data, dict):
                message = data
            elif isinstance(data, str):
                message = json.loads(data)
            else:
                print(f"Unsupported data type: {type(data)}")
                return

            message_type = message.get('type')

            if message_type == 'catalog':
                self.handle_catalog_message(node, message)
            elif message_type == 'search':
                self.handle_search_message(node, message)
            elif message_type == 'search_result':
                self.handle_search_result_message(node, message)
            elif message_type == 'download_request':
                self.handle_download_request(node, message)
            elif message_type == 'file_data':
                self.handle_file_data(node, message)
            elif message_type == 'video_info_request':
                self.handle_video_info_request(node, message)
            elif message_type == 'video_info_response':
                self.handle_video_info_response(node, message)
            elif message_type == 'message':
                # Handle simple message type for interactive mode
                print(f"Message from {node.id}: {message.get('content', '')}")
            else:
                print(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            print("Received invalid JSON data")
        except Exception as e:
            print(f"Error processing message: {e}")

    def send_catalog_to_node(self, node):
        """
        Send the local video catalog to a node.

        Args:
            node: The node to send the catalog to
        """
        catalog_message = {
            'type': 'catalog',
            'node_id': self.id,
            'videos': list(self.video_catalog.keys())
        }

        try:
            self.send_to_node(node, json.dumps(catalog_message))
            print(f"Sent catalog to node {node.id} ({len(self.video_catalog)} videos)")

            # If we already have the other node's catalog, calculate which videos we have that they don't have
            if node.id in self.peers_catalog:
                our_videos = set(self.video_catalog.keys())
                their_videos = set(self.peers_catalog[node.id])
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

        self.peers_catalog[node_id] = videos
        print(f"Received catalog from node {node_id} ({len(videos)} videos)")

        # Calculate which videos the other node has that we don't have
        our_videos = set(self.video_catalog.keys())
        their_videos = set(videos)
        videos_they_have_we_dont = their_videos - our_videos

        if videos_they_have_we_dont:
            print(f"Node {node_id} has {len(videos_they_have_we_dont)} videos that we don't have:")

            # For each video they have that we don't, request video_info
            for video_id in sorted(list(videos_they_have_we_dont)):
                print(f"  - {video_id}")

                # Request video info for this video
                self.request_video_info(node, video_id)
        else:
            print(f"Node {node_id} doesn't have any videos that we don't have")

    def handle_search_message(self, node, message):
        """
        Handle a search message from another node.

        Args:
            node: The node that sent the message
            message: The search message
        """
        search_id = message.get('search_id')
        query = message.get('query')
        video_id = message.get('video_id')

        results = []

        if video_id:
            # Search by video ID
            if video_id in self.video_catalog:
                results.append(self.video_catalog[video_id])
        elif query:
            # Search by query string
            for video_id, metadata in self.video_catalog.items():
                if query.lower() in metadata.get('title', '').lower():
                    results.append(metadata)

        # Send search results back
        result_message = {
            'type': 'search_result',
            'search_id': search_id,
            'node_id': self.id,
            'results': results
        }

        self.send_to_node(node, json.dumps(result_message))
        print(f"Sent {len(results)} search results to node {node.id}")

    def handle_search_result_message(self, node, message):
        """
        Handle a search result message from another node.

        Args:
            node: The node that sent the message
            message: The search result message
        """
        search_id = message.get('search_id')
        node_id = message.get('node_id')
        results = message.get('results', [])

        print(f"Received {len(results)} search results from node {node_id}")

        # Process search results (implementation depends on UI)
        for result in results:
            print(f"Found video: {result.get('title')} ({result.get('video_id')})")

    def handle_download_request(self, node, message):
        """
        Handle a download request from another node.

        Args:
            node: The node that sent the message
            message: The download request message
        """
        video_id = message.get('video_id')
        request_id = message.get('request_id')

        if video_id not in self.video_catalog:
            error_message = {
                'type': 'download_error',
                'request_id': request_id,
                'error': 'Video not found'
            }
            self.send_to_node(node, json.dumps(error_message))
            return

        # Get video content from the API
        video_content = self.get_video_content(video_id)
        if not video_content or 'file_data' not in video_content:
            error_message = {
                'type': 'download_error',
                'request_id': request_id,
                'error': 'Video content not available'
            }
            self.send_to_node(node, json.dumps(error_message))
            return

        # Send file data
        try:
            file_data = video_content['file_data']
            file_hash = video_content['file_hash']
            file_size = video_content['file_size']

            # Send file data
            file_message = {
                'type': 'file_data',
                'request_id': request_id,
                'video_id': video_id,
                'file_hash': file_hash,
                'file_size': file_size,
                'file_data': file_data.hex()  # Convert binary to hex string
            }

            self.send_to_node(node, json.dumps(file_message))
            print(f"Sent file data for video {video_id} to node {node.id}")

        except Exception as e:
            error_message = {
                'type': 'download_error',
                'request_id': request_id,
                'error': str(e)
            }
            self.send_to_node(node, json.dumps(error_message))

    def handle_file_data(self, node, message):
        """
        Handle file data from another node.

        Args:
            node: The node that sent the message
            message: The file data message
        """
        request_id = message.get('request_id')
        video_id = message.get('video_id')
        file_hash = message.get('file_hash')
        file_size = message.get('file_size')
        file_data_hex = message.get('file_data')

        print(f"Received file data for video {video_id} from node {node.id}")

        try:
            # Convert hex string back to binary
            file_data = bytes.fromhex(file_data_hex)

            # Verify file hash
            calculated_hash = hashlib.sha256(file_data).hexdigest()
            if calculated_hash != file_hash:
                print(f"File hash mismatch for video {video_id}")
                return

            # Request the NosVid API to save the file
            # In a real implementation, we would have an API endpoint to upload the file
            # For now, we'll just update our local catalog
            print(f"Received video {video_id} from peer (size: {file_size} bytes)")

            # Get video info from API to update our catalog
            video_info = self.nosvid_api.get_video(video_id)
            if video_info:
                # Update local catalog
                if video_id not in self.video_catalog:
                    self.video_catalog[video_id] = {
                        'video_id': video_id,
                        'title': video_info.get('title', ''),
                        'published_at': video_info.get('published_at', ''),
                        'duration': video_info.get('duration', 0),
                        'file_size': file_size,
                        'file_hash': file_hash,
                        'platforms': video_info.get('platforms', {})
                    }

        except Exception as e:
            print(f"Error processing file data: {e}")

    def handle_video_info_request(self, node, message):
        """
        Handle a video info request from another node.

        Args:
            node: The node that sent the message
            message: The video info request message
        """
        video_id = message.get('video_id')
        request_id = message.get('request_id')

        # Get comprehensive video information from NosVid API
        video_info = None

        # First try to get from NosVid API for most up-to-date and complete information
        api_video_info = self.nosvid_api.get_video(video_id)

        if api_video_info:
            video_info = api_video_info
            print(f"Found video {video_id} in NosVid API")
        elif video_id in self.video_catalog:
            # If not in API, use local catalog
            video_info = self.video_catalog[video_id]
            print(f"Found video {video_id} in local catalog")

        if not video_info:
            error_message = {
                'type': 'video_info_response',
                'request_id': request_id,
                'success': False,
                'error': 'Video not found'
            }
            self.send_to_node(node, json.dumps(error_message))
            return

        # Enhance video info with additional metadata if available
        enhanced_video_info = {
            'video_id': video_id,
            'title': video_info.get('title', ''),
            'published_at': video_info.get('published_at', ''),
            'duration': video_info.get('duration', 0),
            'platforms': video_info.get('platforms', {}),
            'nostr_posts': video_info.get('nostr_posts', []),
            'npubs': video_info.get('npubs', {}),
            'synced_at': video_info.get('synced_at', ''),
            'has_file': False
        }

        # Check if we have the file locally
        if video_id in self.video_catalog:
            platforms = self.video_catalog[video_id].get('platforms', {})
            youtube = platforms.get('youtube', {})
            if youtube.get('downloaded', False):
                enhanced_video_info['has_file'] = True

                # Get file size if available (without loading the entire file)
                try:
                    file_info = self.nosvid_api.get_video_file_content(video_id)
                    if file_info:
                        enhanced_video_info['file_size'] = file_info.get('file_size', 0)
                        enhanced_video_info['file_hash'] = file_info.get('file_hash', '')
                except Exception as e:
                    print(f"Error getting file info for {video_id}: {e}")

        # Send enhanced video info
        response_message = {
            'type': 'video_info_response',
            'request_id': request_id,
            'success': True,
            'video_info': enhanced_video_info
        }

        self.send_to_node(node, json.dumps(response_message))
        print(f"Sent enhanced video info for {video_id} to node {node.id}")

    def request_video_info(self, node, video_id):
        """
        Request video information from another node.

        Args:
            node: The node to request from
            video_id: ID of the video to request information for
        """
        import hashlib
        import time

        # Create a unique request ID
        request_id = hashlib.md5(f"{time.time()}-{video_id}".encode()).hexdigest()

        # Create the request message
        request_message = {
            'type': 'video_info_request',
            'request_id': request_id,
            'video_id': video_id
        }

        # Send the request
        self.send_to_node(node, json.dumps(request_message))
        print(f"Sent video_info request for {video_id} to node {node.id}")

    def handle_video_info_response(self, node, message):
        """
        Handle a video info response from another node.

        Args:
            node: The node that sent the message
            message: The video info response message
        """
        request_id = message.get('request_id')
        success = message.get('success', False)

        if not success:
            error = message.get('error', 'Unknown error')
            print(f"Error getting video info: {error}")
            return

        video_info = message.get('video_info', {})
        video_id = video_info.get('video_id')

        if video_id:
            print(f"\nReceived video info for {video_id} from node {node.id}")
            print("-" * 60)

            # Basic information
            title = video_info.get('title', '')
            published_at = video_info.get('published_at', '')
            duration = video_info.get('duration', 0)

            print(f"Title: {title}")
            print(f"Published at: {published_at}")
            print(f"Duration: {duration} seconds")

            # Platform information
            platforms = video_info.get('platforms', {})
            for platform_name, platform_data in platforms.items():
                print(f"\n{platform_name.capitalize()} information:")
                for key, value in platform_data.items():
                    print(f"  - {key}: {value}")

            # File information
            has_file = video_info.get('has_file', False)
            if has_file:
                print("\nFile information:")
                print(f"  - Available: Yes")
                if 'file_size' in video_info:
                    print(f"  - Size: {video_info.get('file_size')} bytes")
                if 'file_hash' in video_info:
                    print(f"  - Hash: {video_info.get('file_hash')}")
            else:
                print("\nFile information:")
                print(f"  - Available: No")

            # Nostr information
            nostr_posts = video_info.get('nostr_posts', [])
            if nostr_posts:
                print("\nNostr posts:")
                for post in nostr_posts:
                    print(f"  - {post}")

            # NPubs information
            npubs = video_info.get('npubs', {})
            if npubs:
                print("\nNPubs:")
                for source, npub_list in npubs.items():
                    print(f"  - {source}: {', '.join(npub_list)}")

            print("-" * 60)

            # Store the video info in our catalog if we don't have it
            if video_id not in self.video_catalog:
                # Create a simplified version for our catalog
                catalog_entry = {
                    'video_id': video_id,
                    'title': title,
                    'published_at': published_at,
                    'duration': duration,
                    'platforms': platforms,
                    'from_peer': node.id
                }
                self.video_catalog[video_id] = catalog_entry
                print(f"Added video {video_id} to local catalog (from peer {node.id})")

                # Create the video in the local NosVid API
                try:
                    # First, update the basic metadata
                    metadata = {
                        'title': title,
                        'published_at': published_at,
                        'duration': duration,
                        'npubs': npubs,
                        'nostr_posts': nostr_posts,
                        'synced_at': video_info.get('synced_at', '')
                    }

                    metadata_success = self.nosvid_api.update_metadata(video_id, metadata)
                    if metadata_success:
                        print(f"Updated metadata for video {video_id} in local NosVid API")

                    # Then, create platform-specific data
                    youtube_data = platforms.get('youtube', {})
                    if youtube_data:
                        youtube_url = youtube_data.get('url', f"https://www.youtube.com/watch?v={video_id}")
                        youtube_downloaded = youtube_data.get('downloaded', False)
                        youtube_downloaded_at = youtube_data.get('downloaded_at')

                        # Create empty data structure for YouTube platform
                        platform_data = {
                            'metadata': {},
                            'info': {},
                            'description': '',
                            'live_chat': None,
                            'subtitles': {},
                            'description_files': {},
                            'info_files': {},
                            'live_chat_files': {},
                            'thumbnails': [],
                            'video_files': [],
                            'other_files': []
                        }

                        # If the video has additional data, include it
                        if 'data' in youtube_data:
                            platform_data = youtube_data.get('data', platform_data)

                        youtube_success = self.nosvid_api.create_youtube_platform(
                            video_id,
                            youtube_url,
                            platform_data,
                            youtube_downloaded,
                            youtube_downloaded_at
                        )

                        if youtube_success:
                            print(f"Created YouTube platform data for video {video_id} in local NosVid API")

                    # Create nostrmedia data if available
                    nostrmedia_data = platforms.get('nostrmedia', {})
                    if nostrmedia_data and nostrmedia_data.get('url'):
                        nostrmedia_url = nostrmedia_data.get('url')
                        nostrmedia_hash = None  # We don't have this information
                        nostrmedia_uploaded_at = nostrmedia_data.get('uploaded_at')

                        nostrmedia_success = self.nosvid_api.set_nostrmedia_url(
                            video_id,
                            nostrmedia_url,
                            nostrmedia_hash,
                            nostrmedia_uploaded_at
                        )

                        if nostrmedia_success:
                            print(f"Set nostrmedia URL for video {video_id} in local NosVid API")

                    # If the other node has the file and we don't, we could initiate a download
                    if has_file and not youtube_downloaded:
                        print(f"Node {node.id} has the file for video {video_id}. Consider downloading it.")
                        # We could automatically initiate a download here if desired
                        # self.download_video(video_id, node.id)

                except Exception as e:
                    print(f"Error creating video {video_id} in local NosVid API: {e}")

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
                response = self.nosvid_api.list_videos(limit=batch_size, offset=offset)
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
                        self.video_catalog[video_id] = {
                            'video_id': video_id,
                            'title': video.get('title', ''),
                            'published_at': video.get('published_at', ''),
                            'duration': video.get('duration', 0),
                            'platforms': platforms
                        }

            print(f"Loaded {len(self.video_catalog)} downloaded videos out of {total_videos} total videos from NosVid API")

        except Exception as e:
            print(f"Error loading videos from NosVid API: {e}")

    def get_video_content(self, video_id):
        """
        Get the content for a video using the NosVid API.

        Args:
            video_id: ID of the video

        Returns:
            Dictionary with video content and metadata, or None if not found
        """
        return self.nosvid_api.get_video_file_content(video_id)

    def search_videos(self, query=None, video_id=None):
        """
        Search for videos across the network.

        Args:
            query: Search query string
            video_id: Specific video ID to search for

        Returns:
            Search ID for tracking results
        """
        search_id = hashlib.md5(f"{time.time()}-{query}-{video_id}".encode()).hexdigest()

        search_message = {
            'type': 'search',
            'search_id': search_id,
            'query': query,
            'video_id': video_id
        }

        # Send search message to all connected nodes
        for node in self.nodes_outbound:
            self.send_to_node(node, json.dumps(search_message))

        for node in self.nodes_inbound:
            self.send_to_node(node, json.dumps(search_message))

        print(f"Sent search request to {len(self.nodes_outbound) + len(self.nodes_inbound)} nodes")
        return search_id

    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a video.

        Args:
            video_id: ID of the video

        Returns:
            Dictionary containing video information, or None if not found
        """
        # Check local catalog first
        if video_id in self.video_catalog:
            return self.video_catalog[video_id]

        # Try to get from NosVid API
        video_info = self.nosvid_api.get_video(video_id)
        if video_info:
            return video_info

        # Try to get from peers
        for node_id, videos in self.peers_catalog.items():
            if video_id in videos:
                # Find the node
                target_node = None
                for node in self.nodes_outbound:
                    if node.id == node_id:
                        target_node = node
                        break

                for node in self.nodes_inbound:
                    if node.id == node_id:
                        target_node = node
                        break

                if target_node:
                    # Request video info
                    request_id = hashlib.md5(f"{time.time()}-{video_id}".encode()).hexdigest()

                    request_message = {
                        'type': 'video_info_request',
                        'request_id': request_id,
                        'video_id': video_id
                    }

                    self.send_to_node(target_node, json.dumps(request_message))
                    print(f"Sent video info request for {video_id} to node {target_node.id}")

                    # Wait for response (in a real application, this would be handled asynchronously)
                    # For now, just return None and let the caller handle it
                    return None

        return None

    def get_peers(self):
        """
        Get a list of all connected peers.

        Returns:
            List of connected peer nodes
        """
        # Combine inbound and outbound nodes
        return self.nodes_inbound + self.nodes_outbound

    def download_video(self, video_id, node_id=None):
        """
        Download a video from the network.

        Args:
            video_id: ID of the video to download
            node_id: ID of the node to download from (optional)

        Returns:
            Request ID for tracking the download
        """
        # Check if we already have the video
        if video_id in self.video_catalog:
            print(f"Video {video_id} already in local catalog")
            return None

        # Try to download from NosVid API first
        if self.nosvid_api:
            try:
                print(f"Trying to download video {video_id} from NosVid API...")
                success = self.nosvid_api.download_video(video_id)

                if success:
                    print(f"Successfully requested download of video {video_id} from NosVid API")
                    # The video will be added to the catalog during the next sync
                    return None
            except Exception as e:
                print(f"Error downloading video {video_id} from NosVid API: {e}")

        # If NosVid API download failed or not available, try to download from peers
        request_id = hashlib.md5(f"{time.time()}-{video_id}".encode()).hexdigest()

        download_message = {
            'type': 'download_request',
            'request_id': request_id,
            'video_id': video_id
        }

        # Find node that has the video
        target_node = None

        if node_id:
            # Find specific node
            for node in self.nodes_outbound:
                if node.id == node_id:
                    target_node = node
                    break

            for node in self.nodes_inbound:
                if node.id == node_id:
                    target_node = node
                    break
        else:
            # Find any node that has the video
            for node_id, videos in self.peers_catalog.items():
                if video_id in videos:
                    for node in self.nodes_outbound:
                        if node.id == node_id:
                            target_node = node
                            break

                    for node in self.nodes_inbound:
                        if node.id == node_id:
                            target_node = node
                            break

                    if target_node:
                        break

        if not target_node:
            print(f"No node found with video {video_id}")
            return None

        # Send download request
        self.send_to_node(target_node, json.dumps(download_message))
        print(f"Sent download request for video {video_id} to node {target_node.id}")

        # Track active transfer
        self.active_transfers[request_id] = {
            'video_id': video_id,
            'node_id': target_node.id,
            'start_time': time.time(),
            'status': 'requested'
        }

        return request_id

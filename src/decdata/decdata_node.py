#!/usr/bin/env python3
"""
DecData Node - A peer-to-peer node for exchanging video data

This module implements a peer-to-peer node for the DecData project,
which enables decentralized exchange of video data collected by the NosVid project.
It extends the Node class from the p2pnetwork package.
"""

import os
import json
import time
import hashlib
import threading
from typing import Dict, List, Optional, Any, Union
from p2pnetwork.node import Node

from .nosvid_api_client import NosVidAPIClient


class DecDataNode(Node):
    """
    DecData Node for peer-to-peer video data exchange.

    This class extends the Node class from p2pnetwork to implement
    the specific functionality needed for the DecData project.
    """

    def __init__(self, host: str, port: int, share_dir: str = None,
                 nosvid_repo: str = None, nosvid_api_url: str = "http://localhost:2121/api",
                 channel_title: str = "Einundzwanzig Podcast", id: str = None,
                 max_connections: int = 0, sync_interval: int = 300):
        """
        Initialize the DecData node.

        Args:
            host: The host name or ip address to bind to
            port: The port number to bind to
            share_dir: Directory containing videos to share
            nosvid_repo: Path to NosVid repository (optional)
            nosvid_api_url: URL of the NosVid API
            channel_title: Title of the channel
            id: Node ID (optional, will be generated if not provided)
            max_connections: Maximum number of connections (0 for unlimited)
            sync_interval: Interval in seconds for syncing with NosVid API
        """
        super(DecDataNode, self).__init__(host, port, id, None, max_connections)

        # Directory containing videos to share
        self.share_dir = share_dir
        if share_dir and not os.path.exists(share_dir):
            os.makedirs(share_dir, exist_ok=True)

        # Path to NosVid repository
        self.nosvid_repo = nosvid_repo

        # NosVid API client
        self.nosvid_api = NosVidAPIClient(nosvid_api_url)

        # Channel title
        self.channel_title = channel_title

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

        # Start the sync thread if we have a NosVid repository
        if self.nosvid_repo or self.nosvid_api:
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
        """
        while not self.sync_stop_event.is_set():
            try:
                print("Syncing with NosVid API...")

                # Get videos from NosVid API
                response = self.nosvid_api.list_videos(limit=100)
                videos = response.get('videos', [])

                # Update local catalog
                for video in videos:
                    video_id = video.get('video_id')
                    if video_id:
                        # Check if the video has been downloaded
                        platforms = video.get('platforms', {})
                        youtube = platforms.get('youtube', {})

                        if youtube.get('downloaded', False):
                            # Get the file path
                            file_path = self.nosvid_api.get_video_file_path(
                                video_id=video_id,
                                channel_title=self.channel_title,
                                base_dir=self.nosvid_repo or "./repository"
                            )

                            if file_path and os.path.exists(file_path):
                                # Calculate file size and hash
                                file_size = os.path.getsize(file_path)

                                # Add to catalog
                                self.video_catalog[video_id] = {
                                    'video_id': video_id,
                                    'title': video.get('title', ''),
                                    'published_at': video.get('published_at', ''),
                                    'duration': video.get('duration', 0),
                                    'file_path': file_path,
                                    'file_size': file_size,
                                    'platforms': platforms
                                }

                print(f"Synced {len(videos)} videos from NosVid API, {len(self.video_catalog)} in local catalog")

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

    def node_message(self, node, data):
        """
        Event triggered when a message is received from a node.

        Args:
            node: The node that sent the message
            data: The message data
        """
        print(f"Message from node {node.id}: {data[:100]}...")

        try:
            message = json.loads(data)
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

        # Get video file path
        video_path = self.get_video_file_path(video_id)
        if not video_path:
            error_message = {
                'type': 'download_error',
                'request_id': request_id,
                'error': 'Video file not found'
            }
            self.send_to_node(node, json.dumps(error_message))
            return

        # Send file data
        try:
            with open(video_path, 'rb') as f:
                file_data = f.read()

            # Calculate file hash
            file_hash = hashlib.sha256(file_data).hexdigest()

            # Send file data
            file_message = {
                'type': 'file_data',
                'request_id': request_id,
                'video_id': video_id,
                'file_hash': file_hash,
                'file_size': len(file_data),
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

            # Save file
            if self.share_dir:
                output_path = os.path.join(self.share_dir, f"{video_id}.mp4")
                with open(output_path, 'wb') as f:
                    f.write(file_data)

                print(f"Saved video {video_id} to {output_path}")

                # Update local catalog
                if video_id not in self.video_catalog:
                    self.video_catalog[video_id] = {
                        'video_id': video_id,
                        'file_path': output_path,
                        'file_size': file_size,
                        'file_hash': file_hash
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

        if video_id not in self.video_catalog:
            # Try to get the video from NosVid API
            video_info = self.nosvid_api.get_video(video_id)

            if not video_info:
                error_message = {
                    'type': 'video_info_response',
                    'request_id': request_id,
                    'success': False,
                    'error': 'Video not found'
                }
                self.send_to_node(node, json.dumps(error_message))
                return

            # Send video info
            response_message = {
                'type': 'video_info_response',
                'request_id': request_id,
                'success': True,
                'video_info': video_info
            }

            self.send_to_node(node, json.dumps(response_message))
            print(f"Sent video info for {video_id} to node {node.id}")
        else:
            # Send video info from local catalog
            response_message = {
                'type': 'video_info_response',
                'request_id': request_id,
                'success': True,
                'video_info': self.video_catalog[video_id]
            }

            self.send_to_node(node, json.dumps(response_message))
            print(f"Sent video info for {video_id} to node {node.id}")

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
            print(f"Received video info for {video_id} from node {node.id}")
            # Process video info (implementation depends on UI)
            print(f"Video title: {video_info.get('title')}")
            print(f"Published at: {video_info.get('published_at')}")
            print(f"Duration: {video_info.get('duration')} seconds")

    def load_local_catalog(self):
        """
        Load the local video catalog from the share directory and NosVid repository.
        """
        # Load from share directory
        if self.share_dir and os.path.exists(self.share_dir):
            try:
                # Scan share directory for video files
                for filename in os.listdir(self.share_dir):
                    if filename.endswith('.mp4'):
                        video_id = filename.split('.')[0]
                        file_path = os.path.join(self.share_dir, filename)

                        # Get file size
                        file_size = os.path.getsize(file_path)

                        # Calculate file hash
                        with open(file_path, 'rb') as f:
                            file_data = f.read()
                            file_hash = hashlib.sha256(file_data).hexdigest()

                        # Add to catalog
                        self.video_catalog[video_id] = {
                            'video_id': video_id,
                            'file_path': file_path,
                            'file_size': file_size,
                            'file_hash': file_hash
                        }

                print(f"Loaded {len(self.video_catalog)} videos from share directory")

            except Exception as e:
                print(f"Error loading videos from share directory: {e}")

        # Load from NosVid repository
        if self.nosvid_repo and os.path.exists(self.nosvid_repo):
            try:
                # Get videos from NosVid API
                response = self.nosvid_api.list_videos(limit=100)
                videos = response.get('videos', [])

                # Update local catalog
                for video in videos:
                    video_id = video.get('video_id')
                    if video_id:
                        # Check if the video has been downloaded
                        platforms = video.get('platforms', {})
                        youtube = platforms.get('youtube', {})

                        if youtube.get('downloaded', False):
                            # Get the file path
                            file_path = self.nosvid_api.get_video_file_path(
                                video_id=video_id,
                                channel_title=self.channel_title,
                                base_dir=self.nosvid_repo
                            )

                            if file_path and os.path.exists(file_path):
                                # Calculate file size
                                file_size = os.path.getsize(file_path)

                                # Add to catalog
                                self.video_catalog[video_id] = {
                                    'video_id': video_id,
                                    'title': video.get('title', ''),
                                    'published_at': video.get('published_at', ''),
                                    'duration': video.get('duration', 0),
                                    'file_path': file_path,
                                    'file_size': file_size,
                                    'platforms': platforms
                                }

                print(f"Loaded {len(self.video_catalog)} videos from NosVid repository")

            except Exception as e:
                print(f"Error loading videos from NosVid repository: {e}")

    def get_video_file_path(self, video_id):
        """
        Get the file path for a video.

        Args:
            video_id: ID of the video

        Returns:
            Path to the video file, or None if not found
        """
        if video_id in self.video_catalog:
            return self.video_catalog[video_id].get('file_path')

        return None

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

#!/usr/bin/env python3
"""
Test script for the DecData API integration.

This script tests the functionality to send video_info messages and make calls
to the local NosVid API to create data based on content from other nodes.
"""

import os
import sys
import time
import threading
import json
import requests
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the parent directory to sys.path to allow importing the decdata module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from decdata.decdata_node import DecDataNode
from decdata.nosvid_api_client import NosVidAPIClient


class MockResponse:
    """
    Mock response object for requests.
    """
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.content = b"mock_content"

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")


def mock_requests_get(*args, **kwargs):
    """
    Mock for requests.get.
    """
    url = args[0]
    
    if "/videos/" in url and "/file" not in url:
        # Get video endpoint
        video_id = url.split("/")[-1]
        return MockResponse({
            "video_id": video_id,
            "title": f"Mock Video {video_id}",
            "published_at": "2023-01-01T00:00:00Z",
            "duration": 60,
            "platforms": {
                "youtube": {
                    "name": "youtube",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "downloaded": False,
                    "downloaded_at": None,
                    "uploaded": False,
                    "uploaded_at": None
                }
            },
            "nostr_posts": [],
            "npubs": {},
            "synced_at": "2023-01-01T00:00:00Z"
        })
    
    return MockResponse({"error": "Not found"}, 404)


def mock_requests_post(*args, **kwargs):
    """
    Mock for requests.post.
    """
    url = args[0]
    
    if "/update-metadata" in url:
        return MockResponse({"success": True, "message": "Metadata updated"})
    
    if "/platforms/youtube" in url and "/download" not in url:
        return MockResponse({"success": True, "message": "YouTube platform created"})
    
    if "/platforms/nostrmedia" in url and "/upload" not in url:
        return MockResponse({"success": True, "message": "Nostrmedia URL set"})
    
    return MockResponse({"success": False, "message": "Unknown endpoint"}, 404)


def create_mock_video(video_id, title, published_at, duration=60, downloaded=False, nostr_posts=None, npubs=None):
    """
    Create a mock video object with comprehensive metadata.
    """
    return {
        "video_id": video_id,
        "title": title,
        "published_at": published_at,
        "duration": duration,
        "platforms": {
            "youtube": {
                "name": "youtube",
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "downloaded": downloaded,
                "downloaded_at": "2023-01-01T00:00:00Z" if downloaded else None,
                "uploaded": False,
                "uploaded_at": None,
                "data": {
                    "metadata": {"title": title},
                    "info": {"duration": duration},
                    "description": f"Description for {title}",
                    "live_chat": None,
                    "subtitles": {},
                    "description_files": {},
                    "info_files": {},
                    "live_chat_files": {},
                    "thumbnails": [],
                    "video_files": [],
                    "other_files": []
                }
            },
            "nostrmedia": {
                "name": "nostrmedia",
                "url": f"https://nostrmedia.com/v/{video_id}" if downloaded else None,
                "uploaded": downloaded,
                "uploaded_at": "2023-01-02T00:00:00Z" if downloaded else None
            }
        },
        "nostr_posts": nostr_posts or [],
        "npubs": npubs or {},
        "synced_at": "2023-01-03T00:00:00Z"
    }


def run_node(node, duration=30):
    """
    Run a node for a specified duration.
    """
    node.start()
    print(f"Node {node.id} started on port {node.port}")

    try:
        # Keep the node running for the specified duration
        time.sleep(duration)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.join()
        print(f"Node {node.id} stopped")


@patch('requests.get', side_effect=mock_requests_get)
@patch('requests.post', side_effect=mock_requests_post)
def main(mock_post, mock_get):
    """
    Main function to run the test.
    """
    # Create mock videos for node 1
    node1_videos = {
        "video1": create_mock_video(
            "video1", 
            "Video 1", 
            "2023-01-01T00:00:00Z", 
            downloaded=True,
            nostr_posts=["note1abc123", "note2def456"],
            npubs={"description": ["npub1abc123"], "chat": ["npub2def456", "npub3ghi789"]}
        ),
        "video2": create_mock_video(
            "video2", 
            "Video 2", 
            "2023-01-02T00:00:00Z",
            downloaded=False
        ),
        "common1": create_mock_video(
            "common1", 
            "Common Video 1", 
            "2023-01-04T00:00:00Z",
            downloaded=True
        ),
    }

    # Create mock videos for node 2
    node2_videos = {
        "video3": create_mock_video(
            "video3", 
            "Video 3", 
            "2023-01-06T00:00:00Z",
            downloaded=True
        ),
        "video4": create_mock_video(
            "video4", 
            "Video 4", 
            "2023-01-07T00:00:00Z",
            downloaded=False
        ),
        "common1": create_mock_video(
            "common1", 
            "Common Video 1", 
            "2023-01-04T00:00:00Z",
            downloaded=False
        ),
    }

    # Create nodes with real API clients (but mocked requests)
    node1 = DecDataNode(host="127.0.0.1", port=2122)
    node2 = DecDataNode(host="127.0.0.1", port=2123)

    # Load video catalogs
    for video_id, video in node1_videos.items():
        if video.get("platforms", {}).get("youtube", {}).get("downloaded", False):
            node1.video_catalog[video_id] = {
                "video_id": video_id,
                "title": video.get("title", ""),
                "published_at": video.get("published_at", ""),
                "duration": video.get("duration", 0),
                "platforms": video.get("platforms", {})
            }

    for video_id, video in node2_videos.items():
        if video.get("platforms", {}).get("youtube", {}).get("downloaded", False):
            node2.video_catalog[video_id] = {
                "video_id": video_id,
                "title": video.get("title", ""),
                "published_at": video.get("published_at", ""),
                "duration": video.get("duration", 0),
                "platforms": video.get("platforms", {})
            }

    # Create a mock method for handling video_info_request
    original_handle_video_info_request = node2.handle_video_info_request
    
    def mock_handle_video_info_request(node, message):
        video_id = message.get('video_id')
        request_id = message.get('request_id')
        
        # If we have the video in our mock data, use that
        if video_id in node2_videos:
            video_info = node2_videos[video_id]
            
            # Enhance video info with additional metadata
            enhanced_video_info = {
                'video_id': video_id,
                'title': video_info.get('title', ''),
                'published_at': video_info.get('published_at', ''),
                'duration': video_info.get('duration', 0),
                'platforms': video_info.get('platforms', {}),
                'nostr_posts': video_info.get('nostr_posts', []),
                'npubs': video_info.get('npubs', {}),
                'synced_at': video_info.get('synced_at', ''),
                'has_file': video_info.get('platforms', {}).get('youtube', {}).get('downloaded', False)
            }
            
            # Send enhanced video info
            response_message = {
                'type': 'video_info_response',
                'request_id': request_id,
                'success': True,
                'video_info': enhanced_video_info
            }
            
            node2.send_to_node(node, json.dumps(response_message))
            print(f"Sent enhanced video info for {video_id} to node {node.id}")
        else:
            # Fall back to the original method
            original_handle_video_info_request(node, message)
    
    # Replace the method with our mock
    node2.handle_video_info_request = mock_handle_video_info_request

    # Start nodes in separate threads
    node1_thread = threading.Thread(target=run_node, args=(node1, 15))
    node2_thread = threading.Thread(target=run_node, args=(node2, 15))

    node1_thread.start()
    node2_thread.start()

    # Wait for nodes to start
    time.sleep(2)

    # Connect node1 to node2
    print("Connecting node1 to node2...")
    node1.connect_with_node("127.0.0.1", 2123)

    # Wait for connection to establish and catalogs to be exchanged
    time.sleep(10)
    
    # Wait for threads to finish
    node1_thread.join()
    node2_thread.join()


if __name__ == "__main__":
    main()

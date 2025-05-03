#!/usr/bin/env python3
"""
Test script for the enhanced video_info functionality in DecData.

This script starts two DecData nodes with different video catalogs
and tests the video_info request and response functionality.
"""

import os
import sys
import time
import threading
import json
from pathlib import Path

# Add the parent directory to sys.path to allow importing the decdata module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from decdata.decdata_node import DecDataNode


class MockNosVidAPIClient:
    """
    Mock NosVid API client for testing.
    """
    def __init__(self, videos=None):
        self.videos = videos or {}

    def list_videos(self, limit=None, offset=0, sort_by="published_at", sort_order="desc"):
        """
        List videos from the mock API.
        """
        videos_list = list(self.videos.values())
        if sort_by == "published_at":
            videos_list.sort(key=lambda v: v.get("published_at", ""), reverse=(sort_order == "desc"))

        if limit is not None:
            videos_list = videos_list[offset:offset+limit]
        else:
            videos_list = videos_list[offset:]

        return {
            "videos": videos_list,
            "total": len(self.videos),
            "offset": offset,
            "limit": limit
        }

    def get_video(self, video_id):
        """
        Get a video by ID from the mock API.
        """
        return self.videos.get(video_id)

    def get_video_file_content(self, video_id):
        """
        Get the video file content from the mock API.
        """
        video = self.videos.get(video_id)
        if not video:
            return None

        # Check if the video has been downloaded
        platforms = video.get("platforms", {})
        youtube = platforms.get("youtube", {})
        if not youtube.get("downloaded", False):
            return None

        return {
            "video_id": video_id,
            "file_data": b"mock_file_data",
            "file_hash": "mock_file_hash",
            "file_size": 1024,
            "title": video.get("title", ""),
            "published_at": video.get("published_at", ""),
            "duration": video.get("duration", 0),
            "platforms": video.get("platforms", {})
        }


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
                "uploaded_at": None
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


def main():
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

    # Create mock API clients
    node1_api = MockNosVidAPIClient(node1_videos)
    node2_api = MockNosVidAPIClient(node2_videos)

    # Create nodes
    node1 = DecDataNode(host="127.0.0.1", port=2122)
    node2 = DecDataNode(host="127.0.0.1", port=2123)

    # Replace API clients with mock clients
    node1.nosvid_api = node1_api
    node2.nosvid_api = node2_api

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

    # Start nodes in separate threads
    node1_thread = threading.Thread(target=run_node, args=(node1, 30))
    node2_thread = threading.Thread(target=run_node, args=(node2, 30))

    node1_thread.start()
    node2_thread.start()

    # Wait for nodes to start
    time.sleep(2)

    # Connect node1 to node2
    print("Connecting node1 to node2...")
    node1.connect_with_node("127.0.0.1", 2123)

    # Wait for connection to establish
    time.sleep(2)

    # Test video_info request
    print("\nTesting video_info request...")
    
    # Node 1 requests info about video3 from node 2
    request_id = "test_request_1"
    request_message = {
        'type': 'video_info_request',
        'request_id': request_id,
        'video_id': 'video3'
    }
    
    # Get the node object for node2
    node2_obj = None
    for node in node1.nodes_outbound:
        if node.port == 2123:
            node2_obj = node
            break
    
    if node2_obj:
        print(f"Sending video_info request for video3 to node2...")
        node1.send_to_node(node2_obj, json.dumps(request_message))
    
    # Wait for response
    time.sleep(5)
    
    # Node 2 requests info about video1 from node 1
    request_id = "test_request_2"
    request_message = {
        'type': 'video_info_request',
        'request_id': request_id,
        'video_id': 'video1'
    }
    
    # Get the node object for node1
    node1_obj = None
    for node in node2.nodes_inbound:
        if node.port == 2122:
            node1_obj = node
            break
    
    if node1_obj:
        print(f"Sending video_info request for video1 to node1...")
        node2.send_to_node(node1_obj, json.dumps(request_message))
    
    # Wait for response
    time.sleep(5)
    
    # Wait for threads to finish
    node1_thread.join()
    node2_thread.join()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Message Handlers for DecData - Handles different message types

This module provides handlers for different message types in the DecData project.
"""

# Note: This file is split into two parts due to size limitations.
# This is part 1 of the message handlers.

import hashlib
import json
import time
from typing import Any, Dict


def request_video_info(node, target_node, video_id):
    """
    Request video information from another node.

    Args:
        node: The local node
        target_node: The node to request from
        video_id: ID of the video to request information for
    """
    # Create a unique request ID
    request_id = hashlib.md5(f"{time.time()}-{video_id}".encode()).hexdigest()

    # Create the request message
    request_message = {
        "type": "video_info_request",
        "request_id": request_id,
        "video_id": video_id,
    }

    # Send the request
    node.send_to_node(target_node, json.dumps(request_message))
    print(f"Sent video_info request for {video_id} to node {target_node.id}")


def handle_search_message(node, sender_node, message):
    """
    Handle a search message from another node.

    Args:
        node: The local node
        sender_node: The node that sent the message
        message: The search message
    """
    search_id = message.get("search_id")
    query = message.get("query")
    video_id = message.get("video_id")

    results = []

    if video_id:
        # Search by video ID
        if video_id in node.video_catalog:
            results.append(node.video_catalog[video_id])
    elif query:
        # Search by query string
        for video_id, metadata in node.video_catalog.items():
            if query.lower() in metadata.get("title", "").lower():
                results.append(metadata)

    # Send search results back
    result_message = {
        "type": "search_result",
        "search_id": search_id,
        "node_id": node.id,
        "results": results,
    }

    node.send_to_node(sender_node, json.dumps(result_message))
    print(f"Sent {len(results)} search results to node {sender_node.id}")


def handle_search_result_message(node, sender_node, message):
    """
    Handle a search result message from another node.

    Args:
        node: The local node
        sender_node: The node that sent the message
        message: The search result message
    """
    search_id = message.get("search_id")
    node_id = message.get("node_id")
    results = message.get("results", [])

    print(f"Received {len(results)} search results from node {node_id}")

    # Process search results (implementation depends on UI)
    for result in results:
        print(f"Found video: {result.get('title')} ({result.get('video_id')})")


def handle_download_request(node, sender_node, message):
    """
    Handle a download request from another node.

    Args:
        node: The local node
        sender_node: The node that sent the message
        message: The download request message
    """
    video_id = message.get("video_id")
    request_id = message.get("request_id")

    if video_id not in node.video_catalog:
        error_message = {
            "type": "download_error",
            "request_id": request_id,
            "error": "Video not found",
        }
        node.send_to_node(sender_node, json.dumps(error_message))
        return

    # Get video content from the API
    video_content = node.nosvid_api.get_video_file_content(video_id)
    if not video_content or "file_data" not in video_content:
        error_message = {
            "type": "download_error",
            "request_id": request_id,
            "error": "Video content not available",
        }
        node.send_to_node(sender_node, json.dumps(error_message))
        return

    # Send file data
    try:
        file_data = video_content["file_data"]
        file_hash = video_content["file_hash"]
        file_size = video_content["file_size"]

        # Send file data
        file_message = {
            "type": "file_data",
            "request_id": request_id,
            "video_id": video_id,
            "file_hash": file_hash,
            "file_size": file_size,
            "file_data": file_data.hex(),  # Convert binary to hex string
        }

        node.send_to_node(sender_node, json.dumps(file_message))
        print(f"Sent file data for video {video_id} to node {sender_node.id}")

    except Exception as e:
        error_message = {
            "type": "download_error",
            "request_id": request_id,
            "error": str(e),
        }
        node.send_to_node(sender_node, json.dumps(error_message))


def handle_file_data(node, sender_node, message):
    """
    Handle file data from another node.

    Args:
        node: The local node
        sender_node: The node that sent the message
        message: The file data message
    """
    request_id = message.get("request_id")
    video_id = message.get("video_id")
    file_hash = message.get("file_hash")
    file_size = message.get("file_size")
    file_data_hex = message.get("file_data")

    print(f"Received file data for video {video_id} from node {sender_node.id}")

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
        video_info = node.nosvid_api.get_video(video_id)
        if video_info:
            # Update local catalog
            if video_id not in node.video_catalog:
                node.video_catalog[video_id] = {
                    "video_id": video_id,
                    "title": video_info.get("title", ""),
                    "published_at": video_info.get("published_at", ""),
                    "duration": video_info.get("duration", 0),
                    "file_size": file_size,
                    "file_hash": file_hash,
                    "platforms": video_info.get("platforms", {}),
                }

    except Exception as e:
        print(f"Error processing file data: {e}")


def handle_video_info_request(node, sender_node, message):
    """
    Handle a video info request from another node.

    Args:
        node: The local node
        sender_node: The node that sent the message
        message: The video info request message
    """
    video_id = message.get("video_id")
    request_id = message.get("request_id")

    # Get comprehensive video information from NosVid API
    video_info = None

    # First try to get from NosVid API for most up-to-date and complete information
    api_video_info = node.nosvid_api.get_video(video_id)

    if api_video_info:
        video_info = api_video_info
        print(f"Found video {video_id} in NosVid API")
    elif video_id in node.video_catalog:
        # If not in API, use local catalog
        video_info = node.video_catalog[video_id]
        print(f"Found video {video_id} in local catalog")

    if not video_info:
        error_message = {
            "type": "video_info_response",
            "request_id": request_id,
            "success": False,
            "error": "Video not found",
        }
        node.send_to_node(sender_node, json.dumps(error_message))
        return

    # Enhance video info with additional metadata if available
    enhanced_video_info = {
        "video_id": video_id,
        "title": video_info.get("title", ""),
        "published_at": video_info.get("published_at", ""),
        "duration": video_info.get("duration", 0),
        "platforms": video_info.get("platforms", {}),
        "nostr_posts": video_info.get("nostr_posts", []),
        "npubs": video_info.get("npubs", {}),
        "synced_at": video_info.get("synced_at", ""),
        "has_file": False,
    }

    # Check if we have the file locally
    if video_id in node.video_catalog:
        platforms = node.video_catalog[video_id].get("platforms", {})
        youtube = platforms.get("youtube", {})
        if youtube.get("downloaded", False):
            enhanced_video_info["has_file"] = True

            # Get file size if available (without loading the entire file)
            try:
                file_info = node.nosvid_api.get_video_file_content(video_id)
                if file_info:
                    enhanced_video_info["file_size"] = file_info.get("file_size", 0)
                    enhanced_video_info["file_hash"] = file_info.get("file_hash", "")
            except Exception as e:
                print(f"Error getting file info for {video_id}: {e}")

    # Send enhanced video info
    response_message = {
        "type": "video_info_response",
        "request_id": request_id,
        "success": True,
        "video_info": enhanced_video_info,
    }

    node.send_to_node(sender_node, json.dumps(response_message))
    print(f"Sent enhanced video info for {video_id} to node {sender_node.id}")

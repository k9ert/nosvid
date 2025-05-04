#!/usr/bin/env python3
"""
Message Handlers for DecData - Handles different message types

This module provides handlers for different message types in the DecData project.
"""

# Note: This file is split into two parts due to size limitations.
# This is part 2 of the message handlers.

import json


def handle_video_info_response(node, sender_node, message):
    """
    Handle a video info response from another node.

    Args:
        node: The local node
        sender_node: The node that sent the message
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
        print(f"\nReceived video info for {video_id} from node {sender_node.id}")
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
        if video_id not in node.video_catalog:
            # Create a simplified version for our catalog
            catalog_entry = {
                'video_id': video_id,
                'title': title,
                'published_at': published_at,
                'duration': duration,
                'platforms': platforms,
                'from_peer': sender_node.id
            }
            node.video_catalog[video_id] = catalog_entry
            print(f"Added video {video_id} to local catalog (from peer {sender_node.id})")

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

                metadata_success = node.nosvid_api.update_metadata(video_id, metadata)
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

                    youtube_success = node.nosvid_api.create_youtube_platform(
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

                    nostrmedia_success = node.nosvid_api.set_nostrmedia_url(
                        video_id,
                        nostrmedia_url,
                        nostrmedia_hash,
                        nostrmedia_uploaded_at
                    )

                    if nostrmedia_success:
                        print(f"Set nostrmedia URL for video {video_id} in local NosVid API")

                # If the other node has the file and we don't, we could initiate a download
                if has_file and not youtube_downloaded:
                    print(f"Node {sender_node.id} has the file for video {video_id}. Consider downloading it.")
                    # We could automatically initiate a download here if desired
                    # self.download_video(video_id, node.id)

            except Exception as e:
                print(f"Error creating video {video_id} in local NosVid API: {e}")

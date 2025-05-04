"""
Nostr post handling functionality for nosvid
"""

import os
from datetime import datetime
from typing import Any, Dict

from ...utils.filesystem import load_json_file


def check_for_nostr_posts(
    video_dir: str, main_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check for Nostr posts in platform-specific directories and add them to the main metadata

    Args:
        video_dir: Directory containing the video
        main_metadata: Main metadata dictionary

    Returns:
        Updated metadata dictionary
    """
    # Check if the nostr directory exists
    nostr_dir = os.path.join(video_dir, "nostr")
    if not os.path.exists(nostr_dir):
        return main_metadata

    # Initialize platforms dict if it doesn't exist
    if "platforms" not in main_metadata:
        main_metadata["platforms"] = {}

    # Initialize nostr platform if it doesn't exist
    if "nostr" not in main_metadata["platforms"]:
        main_metadata["platforms"]["nostr"] = {"posts": []}
    # If using old format (not array-based), convert to new format
    elif (
        "posts" not in main_metadata["platforms"]["nostr"]
        and "event_id" in main_metadata["platforms"]["nostr"]
    ):
        # Create a post entry from the existing data
        post_entry = {
            "event_id": main_metadata["platforms"]["nostr"]["event_id"],
            "pubkey": main_metadata["platforms"]["nostr"].get("pubkey", ""),
            "nostr_uri": main_metadata["platforms"]["nostr"].get("nostr_uri", ""),
            "links": main_metadata["platforms"]["nostr"].get("links", {}),
            "uploaded_at": main_metadata["platforms"]["nostr"].get(
                "uploaded_at", datetime.now().isoformat()
            ),
        }

        # Create the posts array with the single entry
        main_metadata["platforms"]["nostr"] = {"posts": [post_entry]}

    # Check if the nostr metadata file exists
    nostr_metadata_file = os.path.join(nostr_dir, "metadata.json")
    if os.path.exists(nostr_metadata_file):
        # Load the nostr metadata
        try:
            nostr_metadata = load_json_file(nostr_metadata_file)

            # Check if the nostr metadata has an event_id
            if "event_id" in nostr_metadata:
                event_id = nostr_metadata["event_id"]

                # Check if the event_id is already in the posts array
                event_exists = False
                for post in main_metadata["platforms"]["nostr"].get("posts", []):
                    if post.get("event_id") == event_id:
                        event_exists = True
                        break

                # If the event doesn't exist, add it
                if not event_exists:
                    # Create a new post entry
                    post_entry = {
                        "event_id": event_id,
                        "pubkey": nostr_metadata.get("pubkey", ""),
                        "nostr_uri": nostr_metadata.get("nostr_uri", ""),
                        "links": nostr_metadata.get("links", {}),
                        "uploaded_at": nostr_metadata.get(
                            "uploaded_at", datetime.now().isoformat()
                        ),
                    }

                    # Add the new post to the posts array
                    main_metadata["platforms"]["nostr"]["posts"].append(post_entry)
        except Exception as e:
            print(f"Error loading nostr metadata: {e}")

    # Check for additional nostr metadata files (for multiple posts)
    for item in os.listdir(nostr_dir):
        # Skip the main metadata.json file
        if item == "metadata.json":
            continue

        # Check if it's a JSON file with an event ID as the filename
        if not item.endswith(".json"):
            continue

        # Extract the event ID from the filename (remove .json extension)
        filename_event_id = item[:-5]  # Remove .json extension

        # Load the additional metadata file
        additional_metadata_file = os.path.join(nostr_dir, item)
        try:
            additional_metadata = load_json_file(additional_metadata_file)

            # Use the event ID from the filename if available, otherwise from the metadata
            event_id = filename_event_id

            # Fallback to the event_id in the metadata if needed
            if not event_id and "event_id" in additional_metadata:
                event_id = additional_metadata["event_id"]

                # Check if the event_id is already in the posts array
                event_exists = False
                for post in main_metadata["platforms"]["nostr"].get("posts", []):
                    if post.get("event_id") == event_id:
                        event_exists = True
                        break

                # If the event doesn't exist, add it
                if not event_exists:
                    # Create a new post entry
                    post_entry = {
                        "event_id": event_id,
                        "pubkey": additional_metadata.get("pubkey", ""),
                        "nostr_uri": additional_metadata.get("nostr_uri", ""),
                        "links": additional_metadata.get("links", {}),
                        "uploaded_at": additional_metadata.get(
                            "uploaded_at", datetime.now().isoformat()
                        ),
                    }

                    # Add the new post to the posts array
                    main_metadata["platforms"]["nostr"]["posts"].append(post_entry)
        except Exception as e:
            print(f"Error loading additional nostr metadata: {e}")

    # Sort posts by uploaded_at timestamp (newest first)
    if (
        "nostr" in main_metadata["platforms"]
        and "posts" in main_metadata["platforms"]["nostr"]
    ):
        main_metadata["platforms"]["nostr"]["posts"].sort(
            key=lambda post: post.get("uploaded_at", ""), reverse=True
        )

    return main_metadata

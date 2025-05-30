"""
Nostr platform functionality for nosvid
"""

import logging
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..nostr.upload import upload_to_nostr
from ..utils.config import load_config
from ..utils.filesystem import get_platform_dir, load_json_file, save_json_file

# Set up logging
logger = logging.getLogger(__name__)


def is_platform_activated() -> bool:
    """
    Check if the Nostr platform is activated in the config

    Returns:
        True if the platform is activated, False otherwise
    """
    config = load_config()
    return config.get("nostr", {}).get("activated", False)


def check_platform_activated() -> None:
    """
    Check if the Nostr platform is activated and raise an exception if not

    Raises:
        ValueError: If the platform is not activated
    """
    if not is_platform_activated():
        error_msg = (
            "Nostr platform is not activated. "
            "Please activate it in your config.yaml file by setting nostr.activated = true"
        )
        logger.error(f"Platform activation check failed: {error_msg}")
        logger.error(f"Stack trace: {traceback.format_stack()}")
        raise ValueError(error_msg)


def get_nostr_metadata(video_dir: str) -> Dict[str, Any]:
    """
    Get Nostr metadata for a video

    Args:
        video_dir: Directory containing the video

    Returns:
        Nostr metadata dictionary
    """
    # Get the Nostr platform directory
    nostr_dir = get_platform_dir(video_dir, "nostr")

    # Load Nostr-specific metadata
    nostr_metadata_file = os.path.join(nostr_dir, "metadata.json")
    if os.path.exists(nostr_metadata_file):
        return load_json_file(nostr_metadata_file)

    return {}


def update_nostr_metadata(video_dir: str, metadata: Dict[str, Any]) -> None:
    """
    Update Nostr metadata for a video

    Args:
        video_dir: Directory containing the video
        metadata: Nostr metadata dictionary
    """
    # Get the Nostr platform directory
    nostr_dir = get_platform_dir(video_dir, "nostr")

    # Save Nostr-specific metadata
    nostr_metadata_file = os.path.join(nostr_dir, "metadata.json")
    save_json_file(nostr_metadata_file, metadata)


def get_nostr_posts(video_dir: str) -> List[Dict[str, Any]]:
    """
    Get all Nostr posts for a video

    Args:
        video_dir: Directory containing the video

    Returns:
        List of Nostr post dictionaries
    """
    # Get the Nostr platform directory
    nostr_dir = get_platform_dir(video_dir, "nostr")

    posts = []

    # Check if the nostr directory exists
    if not os.path.exists(nostr_dir):
        return posts

    # Check if the nostr metadata file exists
    nostr_metadata_file = os.path.join(nostr_dir, "metadata.json")
    if os.path.exists(nostr_metadata_file):
        # Load the nostr metadata
        try:
            nostr_metadata = load_json_file(nostr_metadata_file)

            # Check if the nostr metadata has an event_id
            if "event_id" in nostr_metadata:
                # Create a post entry
                post_entry = {
                    "event_id": nostr_metadata["event_id"],
                    "pubkey": nostr_metadata.get("pubkey", ""),
                    "nostr_uri": nostr_metadata.get("nostr_uri", ""),
                    "links": nostr_metadata.get("links", {}),
                    "uploaded_at": nostr_metadata.get(
                        "uploaded_at", datetime.now().isoformat()
                    ),
                }

                posts.append(post_entry)
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

            # Create a post entry
            post_entry = {
                "event_id": event_id,
                "pubkey": additional_metadata.get("pubkey", ""),
                "nostr_uri": additional_metadata.get("nostr_uri", ""),
                "links": additional_metadata.get("links", {}),
                "uploaded_at": additional_metadata.get(
                    "uploaded_at", datetime.now().isoformat()
                ),
            }

            posts.append(post_entry)
        except Exception as e:
            print(f"Error loading additional nostr metadata: {e}")

    # Sort posts by uploaded_at timestamp (newest first)
    posts.sort(key=lambda post: post.get("uploaded_at", ""), reverse=True)

    return posts


def post_video_to_nostr(
    video_id: str,
    title: str,
    description: str,
    video_url: str,
    private_key: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Post a video to Nostr

    Args:
        video_id: ID of the video
        title: Title of the video
        description: Description of the video
        video_url: URL of the video
        private_key: Private key string (hex or nsec format)
        debug: Whether to print debug information

    Returns:
        Dictionary with post result
    """
    # Check if Nostr platform is activated
    check_platform_activated()

    # Log that we're making a Nostr API call
    print(f"Making Nostr API call to post video {video_id}")

    # Post the video to Nostr
    result = upload_to_nostr(
        video_id=video_id,
        title=title,
        description=description,
        video_url=video_url,
        private_key=private_key,
        debug=debug,
    )

    return result

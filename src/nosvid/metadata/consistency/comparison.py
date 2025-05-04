"""
Metadata comparison functionality for nosvid
"""

from datetime import datetime
from typing import Any, Dict, List


def compare_metadata(existing: Dict[str, Any], fresh: Dict[str, Any]) -> List[str]:
    """
    Compare existing and fresh metadata to find differences

    Args:
        existing: Existing metadata
        fresh: Fresh metadata

    Returns:
        List of differences
    """
    differences = []

    # Check basic fields
    for field in ["title", "video_id", "published_at", "duration"]:
        if field in fresh and (
            field not in existing or existing[field] != fresh[field]
        ):
            differences.append(f"Different {field}")

    # Check platforms
    if "platforms" in fresh:
        if "platforms" not in existing:
            differences.append("Missing platforms section")
        else:
            # Check YouTube platform
            if "youtube" in fresh["platforms"]:
                if "youtube" not in existing["platforms"]:
                    differences.append("Missing YouTube platform")
                else:
                    # Check YouTube URL
                    if "url" in fresh["platforms"]["youtube"] and (
                        "url" not in existing["platforms"]["youtube"]
                        or existing["platforms"]["youtube"]["url"]
                        != fresh["platforms"]["youtube"]["url"]
                    ):
                        differences.append("Different YouTube URL")

                    # Check YouTube download status
                    if "downloaded" in fresh["platforms"]["youtube"] and (
                        "downloaded" not in existing["platforms"]["youtube"]
                        or existing["platforms"]["youtube"]["downloaded"]
                        != fresh["platforms"]["youtube"]["downloaded"]
                    ):
                        differences.append("Different YouTube download status")

            # Check nostrmedia platform
            if "nostrmedia" in fresh["platforms"]:
                if "nostrmedia" not in existing["platforms"]:
                    differences.append("Missing nostrmedia platform")
                else:
                    # Check nostrmedia URL
                    if "url" in fresh["platforms"]["nostrmedia"] and (
                        "url" not in existing["platforms"]["nostrmedia"]
                        or existing["platforms"]["nostrmedia"]["url"]
                        != fresh["platforms"]["nostrmedia"]["url"]
                    ):
                        differences.append("Different nostrmedia URL")

            # Preserve nostr posts when generating fresh metadata
            if "nostr" in existing["platforms"]:
                # If nostr platform doesn't exist in fresh metadata, create it
                if "nostr" not in fresh["platforms"]:
                    fresh["platforms"]["nostr"] = {"posts": []}

                # If using old format in existing metadata (not array-based), convert to new format
                if (
                    "posts" not in existing["platforms"]["nostr"]
                    and "event_id" in existing["platforms"]["nostr"]
                ):
                    # Create a post entry from the existing data
                    post_entry = {
                        "event_id": existing["platforms"]["nostr"]["event_id"],
                        "pubkey": existing["platforms"]["nostr"].get("pubkey", ""),
                        "nostr_uri": existing["platforms"]["nostr"].get(
                            "nostr_uri", ""
                        ),
                        "links": existing["platforms"]["nostr"].get("links", {}),
                        "uploaded_at": existing["platforms"]["nostr"].get(
                            "uploaded_at", datetime.now().isoformat()
                        ),
                    }

                    # Add the post to the fresh metadata
                    fresh["platforms"]["nostr"]["posts"].append(post_entry)
                # If using new format in existing metadata (array-based), copy all posts
                elif "posts" in existing["platforms"]["nostr"]:
                    # Initialize posts array if it doesn't exist
                    if "posts" not in fresh["platforms"]["nostr"]:
                        fresh["platforms"]["nostr"]["posts"] = []

                    # Copy all posts from existing metadata
                    for post in existing["platforms"]["nostr"]["posts"]:
                        # Check if the post already exists in fresh metadata
                        event_exists = False
                        for fresh_post in fresh["platforms"]["nostr"].get("posts", []):
                            if fresh_post.get("event_id") == post.get("event_id"):
                                event_exists = True
                                break

                        # If the post doesn't exist, add it
                        if not event_exists:
                            fresh["platforms"]["nostr"]["posts"].append(post)

                    # Sort posts by uploaded_at timestamp (newest first)
                    fresh["platforms"]["nostr"]["posts"].sort(
                        key=lambda post: post.get("uploaded_at", ""), reverse=True
                    )

    # Check npubs
    if "npubs" in fresh:
        if "npubs" not in existing:
            differences.append("Missing npubs section")
        else:
            # Check chat npubs
            if "chat" in fresh["npubs"]:
                if "chat" not in existing["npubs"]:
                    differences.append("Missing chat npubs")
                elif set(fresh["npubs"]["chat"]) != set(existing["npubs"]["chat"]):
                    differences.append("Different chat npubs")

            # Check description npubs
            if "description" in fresh["npubs"]:
                if "description" not in existing["npubs"]:
                    differences.append("Missing description npubs")
                elif set(fresh["npubs"]["description"]) != set(
                    existing["npubs"]["description"]
                ):
                    differences.append("Different description npubs")
    elif "npubs" in existing:
        differences.append("Extra npubs section in existing metadata")

    return differences

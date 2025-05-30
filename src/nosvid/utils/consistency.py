"""
Consistency check functionality for nosvid
"""

import glob
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

from ..metadata.list import generate_metadata_from_files
from ..utils.filesystem import (
    get_video_dir,
    load_json_file,
    save_json_file,
    setup_directory_structure,
)
from ..utils.nostr import process_video_directory


def check_metadata_consistency(
    output_dir: str, channel_title: str, fix_issues: bool = False
) -> Dict[str, Any]:
    """Check for Nostr posts in platform-specific directories and add them to the main metadata"""

    # This is a helper function that will be called for each video directory
    def check_for_nostr_posts(
        video_dir: str, main_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
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

    """
    Check consistency of metadata.json files for all videos

    Args:
        output_dir: Base directory for downloads
        channel_title: Title of the channel
        fix_issues: Whether to fix inconsistencies

    Returns:
        Dictionary with check results
    """
    print(f"Checking metadata consistency in {output_dir} for channel {channel_title}")

    # Set up directory structure
    dirs = setup_directory_structure(output_dir, channel_title)

    # Get all video directories
    videos_dir = dirs["videos_dir"]
    if not os.path.exists(videos_dir):
        print(f"Error: Videos directory not found: {videos_dir}")
        return {"total": 0, "checked": 0, "inconsistencies": 0, "issues": []}

    # Get all subdirectories (video IDs)
    video_dirs = [
        d for d in os.listdir(videos_dir) if os.path.isdir(os.path.join(videos_dir, d))
    ]

    print(f"Found {len(video_dirs)} videos in repository")

    # Process each video directory
    checked = 0
    inconsistencies = 0
    issues = []

    for video_id in video_dirs:
        video_dir = os.path.join(videos_dir, video_id)
        print(
            f"Checking video {checked+1}/{len(video_dirs)}: {video_id}",
            end="",
            flush=True,
        )

        # Check if metadata.json exists
        metadata_file = os.path.join(video_dir, "metadata.json")
        if not os.path.exists(metadata_file):
            print(f" - No metadata.json found")
            if fix_issues:
                print(f"  Creating metadata.json...")
                generate_metadata_from_files(video_dir, video_id)
                print(f"  Created metadata.json")

            issues.append(
                {"video_id": video_id, "issue": "missing_metadata", "fixed": fix_issues}
            )
            inconsistencies += 1
            checked += 1
            continue

        # Load existing metadata
        try:
            existing_metadata = load_json_file(metadata_file)
        except Exception as e:
            print(f" - Error loading metadata.json: {e}")
            issues.append(
                {
                    "video_id": video_id,
                    "issue": "invalid_metadata",
                    "error": str(e),
                    "fixed": False,
                }
            )
            inconsistencies += 1
            checked += 1
            continue

        # Generate fresh metadata
        try:
            fresh_metadata = generate_metadata_from_files(video_dir, video_id)

            # Normalize the published_at date in fresh metadata
            if "published_at" in fresh_metadata and fresh_metadata["published_at"]:
                fresh_metadata["published_at"] = normalize_date(
                    fresh_metadata["published_at"]
                )

            # Also normalize the published_at date in existing metadata for comparison
            if (
                "published_at" in existing_metadata
                and existing_metadata["published_at"]
            ):
                existing_metadata["published_at"] = normalize_date(
                    existing_metadata["published_at"]
                )
        except Exception as e:
            print(f" - Error generating fresh metadata: {e}")
            issues.append(
                {
                    "video_id": video_id,
                    "issue": "generation_error",
                    "error": str(e),
                    "fixed": False,
                }
            )
            inconsistencies += 1
            checked += 1
            continue

        # Process the video directory to extract npubs
        chat_npubs, description_npubs = process_video_directory(video_dir)

        # Add npubs to fresh metadata if found
        if chat_npubs or description_npubs:
            fresh_metadata["npubs"] = {}
            if chat_npubs:
                fresh_metadata["npubs"]["chat"] = chat_npubs
            if description_npubs:
                fresh_metadata["npubs"]["description"] = description_npubs

        # Check for Nostr posts in platform-specific directories
        fresh_metadata = check_for_nostr_posts(video_dir, fresh_metadata)

        # Compare metadata
        differences = compare_metadata(existing_metadata, fresh_metadata)

        if differences:
            print(f" - Found {len(differences)} differences")
            for diff in differences:
                print(f"  - {diff}")

            if fix_issues:
                print(f"  Updating metadata.json...")
                save_json_file(metadata_file, fresh_metadata)
                print(f"  Updated metadata.json")

            issues.append(
                {
                    "video_id": video_id,
                    "issue": "inconsistent_metadata",
                    "differences": differences,
                    "fixed": fix_issues,
                }
            )
            inconsistencies += 1
        else:
            print(f" - OK")

        checked += 1

        # Print progress
        if checked % 10 == 0 or checked == len(video_dirs):
            print(f"Checked {checked}/{len(video_dirs)} videos")

    print("\nConsistency check completed!")
    print(f"Total videos: {len(video_dirs)}")
    print(f"Videos checked: {checked}")
    print(f"Inconsistencies found: {inconsistencies}")

    if inconsistencies > 0:
        print("\nInconsistencies:")
        for i, issue in enumerate(issues, 1):
            video_id = issue["video_id"]
            issue_type = issue["issue"]

            if issue_type == "missing_metadata":
                print(
                    f"{i}. {video_id}: Missing metadata.json file"
                    + (" (fixed)" if issue["fixed"] else "")
                )
            elif issue_type == "invalid_metadata":
                print(f"{i}. {video_id}: Invalid metadata.json file - {issue['error']}")
            elif issue_type == "generation_error":
                print(f"{i}. {video_id}: Error generating metadata - {issue['error']}")
            elif issue_type == "inconsistent_metadata":
                print(
                    f"{i}. {video_id}: Inconsistent metadata - {', '.join(issue['differences'])}"
                    + (" (fixed)" if issue["fixed"] else "")
                )

    return {
        "total": len(video_dirs),
        "checked": checked,
        "inconsistencies": inconsistencies,
        "issues": issues,
    }


def normalize_date(date_str: str) -> str:
    """
    Normalize date format to ISO 8601 (YYYY-MM-DDThh:mm:ssZ)

    Args:
        date_str: Date string to normalize

    Returns:
        Normalized date string
    """
    if not date_str:
        return ""

    # Try different date formats
    from datetime import datetime

    # List of possible formats to try
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 with Z
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO 8601 with microseconds and Z
        "%Y-%m-%dT%H:%M:%S",  # ISO 8601 without Z
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO 8601 with microseconds without Z
        "%Y-%m-%d %H:%M:%S",  # Standard datetime
        "%Y-%m-%d",  # Just date
        "%Y%m%d",  # YYYYMMDD
    ]

    # Try each format
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Return in standard ISO format
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

    # If all formats fail, return the original string
    return date_str


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
    for field in ["title", "video_id", "duration"]:
        if field in fresh and (
            field not in existing or existing[field] != fresh[field]
        ):
            differences.append(f"Different {field}")

    # Special handling for published_at to normalize date formats
    if "published_at" in fresh:
        if "published_at" not in existing:
            differences.append("Missing published_at")
        else:
            # Normalize both dates for comparison
            normalized_existing = normalize_date(existing["published_at"])
            normalized_fresh = normalize_date(fresh["published_at"])

            if normalized_existing != normalized_fresh:
                # Only consider it different if the normalized dates don't match
                differences.append(f"Different published_at")

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

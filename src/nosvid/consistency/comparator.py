"""
Metadata comparison utilities for consistency checking
"""

from datetime import datetime
from typing import Any, Dict, List, Set

from .normalizer import normalize_date


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
    differences.extend(_compare_basic_fields(existing, fresh))

    # Check platforms
    if "platforms" in fresh:
        platform_differences = _compare_platforms(
            existing.get("platforms", {}), fresh.get("platforms", {})
        )
        differences.extend(platform_differences)

    # Check npubs
    if "npubs" in fresh:
        npub_differences = _compare_npubs(
            existing.get("npubs", {}), fresh.get("npubs", {})
        )
        differences.extend(npub_differences)

    return differences


def _compare_basic_fields(existing: Dict[str, Any], fresh: Dict[str, Any]) -> List[str]:
    """
    Compare basic metadata fields

    Args:
        existing: Existing metadata
        fresh: Fresh metadata

    Returns:
        List of differences in basic fields
    """
    differences = []

    # Check simple fields
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

    return differences


def _compare_platforms(
    existing_platforms: Dict[str, Any], fresh_platforms: Dict[str, Any]
) -> List[str]:
    """
    Compare platform-specific metadata

    Args:
        existing_platforms: Existing platforms metadata
        fresh_platforms: Fresh platforms metadata

    Returns:
        List of differences in platform metadata
    """
    differences = []

    if not existing_platforms:
        differences.append("Missing platforms section")
        return differences

    # Check YouTube platform
    if "youtube" in fresh_platforms:
        youtube_differences = _compare_youtube_platform(
            existing_platforms.get("youtube", {}), fresh_platforms.get("youtube", {})
        )
        differences.extend(youtube_differences)

    # Check nostrmedia platform
    if "nostrmedia" in fresh_platforms:
        nostrmedia_differences = _compare_nostrmedia_platform(
            existing_platforms.get("nostrmedia", {}),
            fresh_platforms.get("nostrmedia", {}),
        )
        differences.extend(nostrmedia_differences)

    return differences


def _compare_youtube_platform(
    existing_youtube: Dict[str, Any], fresh_youtube: Dict[str, Any]
) -> List[str]:
    """
    Compare YouTube platform metadata

    Args:
        existing_youtube: Existing YouTube metadata
        fresh_youtube: Fresh YouTube metadata

    Returns:
        List of differences in YouTube metadata
    """
    differences = []

    if not existing_youtube:
        differences.append("Missing YouTube platform")
        return differences

    # Check YouTube URL
    if "url" in fresh_youtube and (
        "url" not in existing_youtube or existing_youtube["url"] != fresh_youtube["url"]
    ):
        differences.append("Different YouTube URL")

    # Check YouTube download status
    if "downloaded" in fresh_youtube and (
        "downloaded" not in existing_youtube
        or existing_youtube["downloaded"] != fresh_youtube["downloaded"]
    ):
        differences.append("Different YouTube download status")

    return differences


def _compare_nostrmedia_platform(
    existing_nostrmedia: Dict[str, Any], fresh_nostrmedia: Dict[str, Any]
) -> List[str]:
    """
    Compare nostrmedia platform metadata

    Args:
        existing_nostrmedia: Existing nostrmedia metadata
        fresh_nostrmedia: Fresh nostrmedia metadata

    Returns:
        List of differences in nostrmedia metadata
    """
    differences = []

    if not existing_nostrmedia:
        differences.append("Missing nostrmedia platform")
        return differences

    # Check nostrmedia URL
    if "url" in fresh_nostrmedia and (
        "url" not in existing_nostrmedia
        or existing_nostrmedia["url"] != fresh_nostrmedia["url"]
    ):
        differences.append("Different nostrmedia URL")

    return differences


def _compare_npubs(
    existing_npubs: Dict[str, List[str]], fresh_npubs: Dict[str, List[str]]
) -> List[str]:
    """
    Compare npubs metadata

    Args:
        existing_npubs: Existing npubs metadata
        fresh_npubs: Fresh npubs metadata

    Returns:
        List of differences in npubs metadata
    """
    differences = []

    # If there are no existing npubs, we don't consider it a difference
    # This is because we're generating fresh metadata and adding npubs to it
    if not existing_npubs:
        return differences

    # Check chat npubs
    if "chat" in fresh_npubs:
        if "chat" not in existing_npubs:
            differences.append("Missing chat npubs")
        elif set(fresh_npubs["chat"]) != set(existing_npubs["chat"]):
            differences.append("Different chat npubs")

    # Check description npubs
    if "description" in fresh_npubs:
        if "description" not in existing_npubs:
            differences.append("Missing description npubs")
        elif set(fresh_npubs["description"]) != set(existing_npubs["description"]):
            differences.append("Different description npubs")

    return differences

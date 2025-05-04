"""
Listing functionality for nosvid
"""

import glob
import json
import os
from datetime import datetime

from ..utils.filesystem import (
    get_platform_dir,
    get_video_dir,
    load_json_file,
    save_json_file,
)

# ANSI color codes
COLORS = {
    "ORANGE": "\033[38;5;208m",  # Orange color
    "RESET": "\033[0m",  # Reset to default color
}


def generate_metadata_from_files(video_dir, video_id):
    """
    Generate metadata.json from existing files in the video directory

    Args:
        video_dir: Directory containing the video files
        video_id: ID of the video

    Returns:
        Dictionary with metadata
    """
    # Create platform-specific directory for YouTube
    youtube_dir = get_platform_dir(video_dir, "youtube")

    # Default YouTube metadata
    youtube_metadata = {
        "title": f"Video {video_id}",
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "published_at": "",
        "synced_at": datetime.now().isoformat(),
        "downloaded": False,
    }

    # Try to get title and other info from info.json
    info_files = glob.glob(os.path.join(youtube_dir, "*.info.json"))
    if info_files:
        try:
            with open(info_files[0], "r", encoding="utf-8") as f:
                info = json.load(f)
                if "title" in info:
                    youtube_metadata["title"] = info["title"]
                if "upload_date" in info:
                    # Convert YYYYMMDD to ISO format
                    upload_date = info["upload_date"]
                    if len(upload_date) == 8:
                        date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}T00:00:00Z"
                        # Import the normalize_date function
                        from ..utils.consistency import normalize_date

                        youtube_metadata["published_at"] = normalize_date(date_str)
                # Extract duration in seconds
                if "duration" in info:
                    youtube_metadata["duration"] = info["duration"]
        except (json.JSONDecodeError, IOError):
            pass

    # Check if video is downloaded
    video_files = (
        glob.glob(os.path.join(youtube_dir, "*.mp4"))
        + glob.glob(os.path.join(youtube_dir, "*.webm"))
        + glob.glob(os.path.join(youtube_dir, "*.mkv"))
    )
    youtube_metadata["downloaded"] = len(video_files) > 0

    # Save the YouTube metadata file
    youtube_metadata_file = os.path.join(youtube_dir, "metadata.json")
    save_json_file(youtube_metadata_file, youtube_metadata)

    # Create main metadata with references to all platforms
    main_metadata = {
        "title": youtube_metadata["title"],
        "video_id": video_id,
        "published_at": youtube_metadata["published_at"],
        "duration": youtube_metadata.get("duration", 0),  # Add duration field
        "synced_at": datetime.now().isoformat(),
        "platforms": {
            "youtube": {
                "url": youtube_metadata["url"],
                "downloaded": youtube_metadata["downloaded"],
            }
        },
    }

    # Check for nostrmedia platform
    nostrmedia_dir = os.path.join(video_dir, "nostrmedia")
    if os.path.exists(nostrmedia_dir):
        nostrmedia_metadata_file = os.path.join(nostrmedia_dir, "metadata.json")
        if os.path.exists(nostrmedia_metadata_file):
            nostrmedia_metadata = load_json_file(nostrmedia_metadata_file)
            main_metadata["platforms"]["nostrmedia"] = {
                "url": nostrmedia_metadata.get("url", ""),
                "hash": nostrmedia_metadata.get("hash", ""),
                "uploaded_at": nostrmedia_metadata.get("uploaded_at", ""),
            }

    # Check for nostr platform
    nostr_dir = os.path.join(video_dir, "nostr")
    if os.path.exists(nostr_dir):
        nostr_metadata_file = os.path.join(nostr_dir, "metadata.json")
        if os.path.exists(nostr_metadata_file):
            nostr_metadata = load_json_file(nostr_metadata_file)

            # Initialize nostr platform with posts array
            main_metadata["platforms"]["nostr"] = {"posts": []}

            # Add the post from the metadata file
            if "event_id" in nostr_metadata:
                post_entry = {
                    "event_id": nostr_metadata.get("event_id", ""),
                    "pubkey": nostr_metadata.get("pubkey", ""),
                    "nostr_uri": nostr_metadata.get("nostr_uri", ""),
                    "links": nostr_metadata.get("links", {}),
                    "uploaded_at": nostr_metadata.get(
                        "uploaded_at", datetime.now().isoformat()
                    ),
                }
                main_metadata["platforms"]["nostr"]["posts"].append(post_entry)

    # Save the main metadata file
    main_metadata_file = os.path.join(video_dir, "metadata.json")
    save_json_file(main_metadata_file, main_metadata)

    return main_metadata


def list_videos(
    videos_dir,
    metadata_dir=None,
    channel_id=None,
    show_downloaded=True,
    show_not_downloaded=True,
):
    """
    List all videos in the repository

    Args:
        videos_dir: Directory containing videos
        metadata_dir: Directory containing metadata (for cache access)
        channel_id: ID of the channel (for cache access)
        show_downloaded: Whether to show downloaded videos
        show_not_downloaded: Whether to show videos that have not been downloaded

    Returns:
        Tuple of (videos list, stats dictionary)
    """
    if not os.path.exists(videos_dir):
        print(f"Videos directory not found: {videos_dir}")
        return [], {}

    videos = []
    stats = {
        "total_in_cache": 0,
        "total_with_metadata": 0,
        "total_downloaded": 0,
        "total_uploaded_nm": 0,
        "total_posted_nostr": 0,
        "total_with_npubs": 0,
        "total_npubs": 0,
    }

    # Get the total number of videos in cache if metadata_dir and channel_id are provided
    if metadata_dir and channel_id:
        cache_file = os.path.join(metadata_dir, f"channel_videos_{channel_id}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                stats["total_in_cache"] = cache_data.get("video_count", 0)
            except Exception as e:
                print(f"Error reading cache: {e}")

    # Count videos with metadata
    if os.path.exists(videos_dir):
        stats["total_with_metadata"] = sum(
            1
            for item in os.listdir(videos_dir)
            if os.path.isdir(os.path.join(videos_dir, item))
        )

    for video_id in os.listdir(videos_dir):
        video_dir = get_video_dir(videos_dir, video_id)

        if not os.path.isdir(video_dir):
            continue

        main_metadata_file = os.path.join(video_dir, "metadata.json")

        # If metadata.json doesn't exist, try to generate it from existing files
        if not os.path.exists(main_metadata_file):
            print(f"Generating metadata for video: {video_id}")
            main_metadata = generate_metadata_from_files(video_dir, video_id)
        else:
            main_metadata = load_json_file(main_metadata_file)

        # Check if YouTube platform exists and get download status
        youtube_downloaded = False
        if "platforms" in main_metadata and "youtube" in main_metadata["platforms"]:
            youtube_downloaded = main_metadata["platforms"]["youtube"].get(
                "downloaded", False
            )
            if youtube_downloaded:
                stats["total_downloaded"] += 1

        # Filter based on download status
        if youtube_downloaded and not show_downloaded:
            continue

        if not youtube_downloaded and not show_not_downloaded:
            continue

        # Check if nostrmedia platform exists
        has_nostrmedia = (
            "platforms" in main_metadata and "nostrmedia" in main_metadata["platforms"]
        )
        nostrmedia_url = ""
        if has_nostrmedia:
            nostrmedia_url = main_metadata["platforms"]["nostrmedia"].get("url", "")
            if nostrmedia_url:
                stats["total_uploaded_nm"] += 1

        # Check if nostr platform exists and count posts
        nostr_post_count = 0
        if "platforms" in main_metadata and "nostr" in main_metadata["platforms"]:
            nostr_data = main_metadata["platforms"]["nostr"]
            # Check for posts array (new format)
            if "posts" in nostr_data:
                nostr_post_count = len(nostr_data["posts"])
            # Check for event_id (old format)
            elif "event_id" in nostr_data:
                nostr_post_count = 1

            # Update stats if posts were found
            if nostr_post_count > 0:
                stats["total_posted_nostr"] = stats.get("total_posted_nostr", 0) + 1

        # Count npubs if they exist in metadata
        npub_count = 0
        if "npubs" in main_metadata:
            # Count npubs in chat
            if "chat" in main_metadata["npubs"]:
                npub_count += len(main_metadata["npubs"]["chat"])
            # Count npubs in description
            if "description" in main_metadata["npubs"]:
                npub_count += len(main_metadata["npubs"]["description"])

            # Update stats if npubs were found
            if npub_count > 0:
                stats["total_with_npubs"] += 1
                stats["total_npubs"] += npub_count

        videos.append(
            {
                "video_id": video_id,
                "title": main_metadata.get("title", "Unknown"),
                "published_at": main_metadata.get("published_at", ""),
                "duration": main_metadata.get("duration", 0),  # Add duration field
                "downloaded": youtube_downloaded,
                "url": main_metadata.get("platforms", {})
                .get("youtube", {})
                .get("url", ""),
                "nostrmedia_url": nostrmedia_url,
                "nostr_post_count": nostr_post_count,  # Add nostr post count
                "npub_count": npub_count,  # Add npub count
            }
        )

    # Sort by published date (oldest first)
    videos.sort(key=lambda x: x.get("published_at", ""), reverse=False)

    return videos, stats


def print_video_list(videos, stats=None, show_index=True):
    """
    Print a list of videos and repository status summary

    Args:
        videos: List of video dictionaries
        stats: Dictionary with repository statistics
        show_index: Whether to show the index number
    """
    # Print repository status summary if stats are provided
    if stats:
        print("\nRepository Status:")
        print("-" * 60)

        total_in_cache = stats.get("total_in_cache", 0)
        total_with_metadata = stats.get("total_with_metadata", 0)
        total_downloaded = stats.get("total_downloaded", 0)
        total_uploaded_nm = stats.get("total_uploaded_nm", 0)
        total_posted_nostr = stats.get("total_posted_nostr", 0)
        total_with_npubs = stats.get("total_with_npubs", 0)
        total_npubs = stats.get("total_npubs", 0)

        # Calculate percentages
        metadata_percent = (
            (total_with_metadata / total_in_cache * 100) if total_in_cache > 0 else 0
        )
        downloaded_percent = (
            (total_downloaded / total_in_cache * 100) if total_in_cache > 0 else 0
        )
        uploaded_nm_percent = (
            (total_uploaded_nm / total_in_cache * 100) if total_in_cache > 0 else 0
        )
        posted_nostr_percent = (
            (total_posted_nostr / total_in_cache * 100) if total_in_cache > 0 else 0
        )
        npubs_percent = (
            (total_with_npubs / total_in_cache * 100) if total_in_cache > 0 else 0
        )

        print(f"Videos in cache (YT):     {total_in_cache}")
        print(
            f"Metadata (YT):            {total_with_metadata:4d} / {total_in_cache} ({metadata_percent:.1f}%)"
        )
        print(
            f"Downloaded (YT):          {total_downloaded:4d} / {total_in_cache} ({downloaded_percent:.1f}%)"
        )
        print(
            f"Uploaded (NM):            {total_uploaded_nm:4d} / {total_in_cache} ({uploaded_nm_percent:.1f}%)"
        )
        print(
            f"Posted (NS):              {total_posted_nostr:4d} / {total_in_cache} ({posted_nostr_percent:.1f}%)"
        )
        print(
            f"Videos with npubs:        {total_with_npubs:4d} / {total_in_cache} ({npubs_percent:.1f}%)"
        )
        print(f"Total npubs found:        {total_npubs}")
        print("-" * 60)

    if not videos:
        print("No videos found.")
        return

    print(f"\nFound {len(videos)} videos:")
    print("-" * 100)

    for i, video in enumerate(videos, 1):
        yt_status = "✓" if video["downloaded"] else " "
        nm_status = "✓" if video.get("nostrmedia_url") else " "

        # Format the Nostr post status
        nostr_post_count = video.get("nostr_post_count", 0)
        if nostr_post_count == 0:
            ns_status = " "
        elif nostr_post_count == 1:
            ns_status = "✓"
        else:
            ns_status = str(nostr_post_count)

        # Format the date
        published = (
            video.get("published_at", "")[:10]
            if video.get("published_at")
            else "Unknown"
        )

        # Format the duration in minutes
        duration_seconds = video.get("duration", 0)
        duration_minutes = (
            round(duration_seconds / 60, 1) if duration_seconds > 0 else 0
        )
        duration_str = f"{duration_minutes:.1f} min" if duration_minutes > 0 else ""

        # Create engagement bar based on npub count
        npub_count = video.get("npub_count", 0)
        # Cap at 10 for display purposes
        display_count = min(npub_count, 10)
        # Create the engagement bar with orange blocks (using unicode block character)
        orange_blocks = f"{COLORS['ORANGE']}{'█' * display_count}{COLORS['RESET']}"
        engagement_bar = f"[{orange_blocks}{' ' * (10 - display_count)}]"

        # Format the output
        if show_index:
            print(
                f"{i:3d}. [YT:{yt_status}|NM:{nm_status}|NS:{ns_status}] {video['video_id']} ({published}) {engagement_bar} {duration_str} - {video['title']}"
            )
        else:
            print(
                f"[YT:{yt_status}|NM:{nm_status}|NS:{ns_status}] {video['video_id']} ({published}) {engagement_bar} {duration_str} - {video['title']}"
            )

    print("-" * 100)

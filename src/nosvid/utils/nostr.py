"""
Nostr-related utility functions
"""

import json
import os
import re
from typing import Any, Dict, List, Tuple


def extract_npubs_from_text(text: str) -> List[str]:
    """
    Extract npubs from text content

    Args:
        text: Text content to search for npubs

    Returns:
        List of unique npubs found in the text
    """
    # Regular expression to match npub format (npub followed by 1 and 59-60 alphanumeric characters)
    # We use word boundaries to ensure we get complete npubs
    npub_pattern = r"\bnpub1[a-zA-Z0-9]{59,60}\b"

    # Find all matches
    npubs = re.findall(npub_pattern, text)

    # If no matches with strict pattern, try a more lenient one
    if not npubs:
        # Try without word boundaries and with a more flexible length
        npub_pattern = r"npub1[a-zA-Z0-9]{58,64}"
        npubs = re.findall(npub_pattern, text)

    # Return unique npubs
    return list(set(npubs))


def extract_npubs_from_chat_json(chat_file_path: str) -> List[str]:
    """
    Extract npubs from a YouTube live chat JSON file

    Args:
        chat_file_path: Path to the chat JSON file

    Returns:
        List of unique npubs found in the chat
    """
    npubs = []

    try:
        # Simply read the file line by line and extract npubs using regex
        with open(chat_file_path, "r", encoding="utf-8") as f:
            for line in f:
                # Extract npubs from each line
                line_npubs = extract_npubs_from_text(line)
                if line_npubs:
                    npubs.extend(line_npubs)
                    print(f"Found npubs in chat: {line_npubs}")
    except Exception as e:
        print(f"Warning: Could not process chat file {chat_file_path}: {e}")

    # Return unique npubs
    return list(set(npubs))


def process_video_directory(video_dir: str) -> Tuple[List[str], List[str]]:
    """
    Process a video directory to extract npubs from chat and description files

    Args:
        video_dir: Path to the video directory

    Returns:
        Tuple of (chat_npubs, description_npubs)
    """
    chat_npubs = []
    description_npubs = []

    # Check if the directory exists
    if not os.path.exists(video_dir):
        print(f"Directory does not exist: {video_dir}")
        return chat_npubs, description_npubs

    # Get video ID from directory name
    video_id = os.path.basename(video_dir)

    # Process YouTube subdirectory
    youtube_dir = os.path.join(video_dir, "youtube")
    if os.path.exists(youtube_dir):
        # Find chat files
        chat_files = [
            f for f in os.listdir(youtube_dir) if f.endswith(".live_chat.json")
        ]
        if chat_files:
            print(f"Found {len(chat_files)} chat file(s) for video {video_id}")
            for chat_file in chat_files:
                chat_file_path = os.path.join(youtube_dir, chat_file)
                print(f"Processing chat file: {chat_file}")
                file_npubs = extract_npubs_from_chat_json(chat_file_path)
                if file_npubs:
                    print(f"Found {len(file_npubs)} npubs in chat file")
                    chat_npubs.extend(file_npubs)

        # Find description files
        description_files = [
            f for f in os.listdir(youtube_dir) if f.endswith(".description")
        ]
        if description_files:
            print(
                f"Found {len(description_files)} description file(s) for video {video_id}"
            )
            for desc_file in description_files:
                desc_file_path = os.path.join(youtube_dir, desc_file)
                print(f"Processing description file: {desc_file}")
                try:
                    with open(desc_file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        file_npubs = extract_npubs_from_text(content)
                        if file_npubs:
                            print(f"Found {len(file_npubs)} npubs in description file")
                            description_npubs.extend(file_npubs)
                except Exception as e:
                    print(
                        f"Warning: Could not process description file {desc_file_path}: {e}"
                    )
    else:
        print(f"YouTube directory not found for video {video_id}")

    # Return unique npubs
    return list(set(chat_npubs)), list(set(description_npubs))

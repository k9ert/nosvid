"""
Base module for command-related functionality
"""

from ...utils.config import get_default_output_dir, get_default_video_quality, get_default_download_delay

# Dictionary mapping channel IDs to their titles
CHANNEL_MAPPING = {
    "UCxSRxq14XIoMbFDEjMOPU5Q": "Einundzwanzig"
}

def get_channel_title():
    """
    Get the channel title from the config file or hardcoded mapping

    Returns:
        str: Channel title
    """
    # Use the hardcoded channel title for now
    return CHANNEL_MAPPING.get("UCxSRxq14XIoMbFDEjMOPU5Q", "Unknown")

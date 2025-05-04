"""
HeyGen platform functionality for nosvid
"""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from ..utils.config import read_api_key_from_yaml
from ..utils.filesystem import get_platform_dir, load_json_file, save_json_file


def get_heygen_metadata(video_dir: str, quality: str = "scale") -> Dict[str, Any]:
    """
    Get HeyGen metadata for a video

    Args:
        video_dir: Directory containing the video
        quality: Quality level of the translation ('free', 'pro', 'scale')

    Returns:
        HeyGen metadata dictionary
    """
    # Get the HeyGen platform directory
    heygen_dir = get_platform_dir(video_dir, "heygen")

    # Create quality-specific directory
    quality_dir = os.path.join(heygen_dir, quality)
    os.makedirs(quality_dir, exist_ok=True)

    # Load HeyGen-specific metadata
    heygen_metadata_file = os.path.join(quality_dir, "metadata.json")
    if os.path.exists(heygen_metadata_file):
        return load_json_file(heygen_metadata_file)

    return {}


def update_heygen_metadata(
    video_dir: str, metadata: Dict[str, Any], quality: str = "scale"
) -> None:
    """
    Update HeyGen metadata for a video

    Args:
        video_dir: Directory containing the video
        metadata: HeyGen metadata dictionary
        quality: Quality level of the translation ('free', 'pro', 'scale')
    """
    # Get the HeyGen platform directory
    heygen_dir = get_platform_dir(video_dir, "heygen")

    # Create quality-specific directory
    quality_dir = os.path.join(heygen_dir, quality)
    os.makedirs(quality_dir, exist_ok=True)

    # Save HeyGen-specific metadata
    heygen_metadata_file = os.path.join(quality_dir, "metadata.json")
    save_json_file(heygen_metadata_file, metadata)


def list_supported_languages(api_key: str) -> List[str]:
    """
    List supported languages for HeyGen video translation

    Args:
        api_key: HeyGen API key

    Returns:
        List of supported languages
    """
    url = "https://api.heygen.com/v2/video_translate/target_languages"
    headers = {"accept": "application/json", "x-api-key": api_key}

    try:
        response = requests.get(url, headers=headers)

        # Check for 403 Forbidden specifically
        if response.status_code == 403:
            print("Error: Access to Video Translation API is forbidden.")
            print(
                "The Video Translation API is only available on Scale ($330/month) and Enterprise plans."
            )
            print("You are currently on the Free or Pro plan.")
            print("\nAvailable languages for reference:")
            return [
                "English",
                "Spanish",
                "French",
                "German",
                "Italian",
                "Portuguese",
                "Dutch",
                "Russian",
                "Japanese",
                "Korean",
                "Chinese",
                "Arabic",
                "Hindi",
                "Turkish",
                "Polish",
                "Swedish",
                "Norwegian",
                "Danish",
                "Finnish",
                "Greek",
                "Czech",
                "Hungarian",
                "Romanian",
                "Bulgarian",
                "Croatian",
                "Serbian",
                "Slovak",
                "Slovenian",
                "Ukrainian",
                "Hebrew",
                "Thai",
                "Vietnamese",
                "Indonesian",
                "Malay",
                "Filipino",
                "Bengali",
                "Urdu",
                "Persian",
                "Swahili",
            ]

        response.raise_for_status()
        data = response.json()

        if data.get("error") is not None:
            print(f"Error: {data['error']}")
            return []

        return data["data"]["languages"]
    except Exception as e:
        print(f"Error listing supported languages: {str(e)}")
        return []


def translate_video(
    video_url: str, output_language: str, title: str, api_key: str, debug: bool = False
) -> Dict[str, Any]:
    """
    Translate a video using HeyGen

    Args:
        video_url: URL of the video to translate
        output_language: Target language for translation
        title: Title for the translated video
        api_key: HeyGen API key
        debug: Whether to print debug information

    Returns:
        Dictionary with translation result
    """
    url = "https://api.heygen.com/v2/video_translate"
    headers = {
        "accept": "application/json",
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "video_url": video_url,
        "output_language": output_language,
        "title": title,
    }

    if debug:
        print(f"Sending request to HeyGen API: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=payload)

        # Check for 403 Forbidden specifically
        if response.status_code == 403:
            print("Error: Access to Video Translation API is forbidden.")
            print(
                "The Video Translation API is only available on Scale ($330/month) and Enterprise plans."
            )
            print("You are currently on the Free or Pro plan.")
            print("Please upgrade your plan to use this feature.")
            return {
                "success": False,
                "error": "Access to Video Translation API is forbidden",
                "message": "The Video Translation API is only available on Scale and Enterprise plans",
            }

        response.raise_for_status()
        data = response.json()

        if data.get("error") is not None:
            return {
                "success": False,
                "error": data["error"],
                "message": "Failed to start translation",
            }

        result = {
            "success": True,
            "video_translate_id": data["data"]["video_translate_id"],
            "requested_at": datetime.now().isoformat(),
            "output_language": output_language,
            "title": title,
            "status": "pending",
        }

        if debug:
            print(f"Translation request successful: {json.dumps(result, indent=2)}")

        return result
    except Exception as e:
        error_message = str(e)
        if debug:
            print(f"Error translating video: {error_message}")

        return {
            "success": False,
            "error": error_message,
            "message": "Failed to start translation",
        }


def check_translation_status(
    video_translate_id: str, api_key: str, debug: bool = False
) -> Dict[str, Any]:
    """
    Check the status of a video translation

    Args:
        video_translate_id: ID of the translation job
        api_key: HeyGen API key
        debug: Whether to print debug information

    Returns:
        Dictionary with translation status
    """
    url = f"https://api.heygen.com/v2/video_translate/{video_translate_id}"
    headers = {"accept": "application/json", "x-api-key": api_key}

    try:
        response = requests.get(url, headers=headers)

        # Check for 403 Forbidden specifically
        if response.status_code == 403:
            print("Error: Access to Video Translation API is forbidden.")
            print(
                "The Video Translation API is only available on Scale ($330/month) and Enterprise plans."
            )
            print("You are currently on the Free or Pro plan.")
            print("Please upgrade your plan to use this feature.")
            return {
                "success": False,
                "error": "Access to Video Translation API is forbidden",
                "message": "The Video Translation API is only available on Scale and Enterprise plans",
            }

        response.raise_for_status()
        data = response.json()

        if data.get("error") is not None:
            return {
                "success": False,
                "error": data["error"],
                "message": "Failed to check translation status",
            }

        status_data = data["data"]
        result = {
            "success": True,
            "video_translate_id": status_data["video_translate_id"],
            "title": status_data["title"],
            "status": status_data["status"],
            "checked_at": datetime.now().isoformat(),
        }

        if status_data["status"] == "success" and status_data.get("url"):
            result["url"] = status_data["url"]

        if status_data.get("message"):
            result["message"] = status_data["message"]

        if debug:
            print(f"Translation status: {json.dumps(result, indent=2)}")

        return result
    except Exception as e:
        error_message = str(e)
        if debug:
            print(f"Error checking translation status: {error_message}")

        return {
            "success": False,
            "error": error_message,
            "message": "Failed to check translation status",
        }


def wait_for_translation(
    video_translate_id: str,
    api_key: str,
    timeout: int = 3600,
    check_interval: int = 30,
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Wait for a video translation to complete

    Args:
        video_translate_id: ID of the translation job
        api_key: HeyGen API key
        timeout: Maximum time to wait in seconds (default: 1 hour)
        check_interval: Time between status checks in seconds
        debug: Whether to print debug information

    Returns:
        Dictionary with translation result
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = check_translation_status(video_translate_id, api_key, debug)

        if not status["success"]:
            return status

        if status["status"] == "success":
            return status

        if status["status"] == "failed":
            return {
                "success": False,
                "error": status.get("message", "Translation failed"),
                "status": "failed",
            }

        # Still processing, wait and check again
        if debug:
            print(
                f"Translation in progress, status: {status['status']}. Checking again in {check_interval} seconds..."
            )

        time.sleep(check_interval)

    return {
        "success": False,
        "error": f"Timeout after {timeout} seconds",
        "message": "Translation timed out",
    }


# ISO language code mapping
LANGUAGE_TO_ISO = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Russian": "ru",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
    "Arabic": "ar",
    "Hindi": "hi",
    "Turkish": "tr",
    "Polish": "pl",
    "Swedish": "sv",
    "Norwegian": "no",
    "Danish": "da",
    "Finnish": "fi",
    "Greek": "el",
    "Czech": "cs",
    "Hungarian": "hu",
    "Romanian": "ro",
    "Bulgarian": "bg",
    "Croatian": "hr",
    "Serbian": "sr",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Ukrainian": "uk",
    "Hebrew": "he",
    "Thai": "th",
    "Vietnamese": "vi",
    "Indonesian": "id",
    "Malay": "ms",
    "Filipino": "fil",
    "Bengali": "bn",
    "Urdu": "ur",
    "Persian": "fa",
    "Swahili": "sw",
}

# Reverse mapping from ISO to language name
ISO_TO_LANGUAGE = {v: k for k, v in LANGUAGE_TO_ISO.items()}


def get_iso_code(language: str) -> str:
    """
    Get ISO language code for a language name

    Args:
        language: Language name

    Returns:
        ISO language code or original string if not found
    """
    # If it's already an ISO code, return it
    if language.lower() in [code.lower() for code in ISO_TO_LANGUAGE.keys()]:
        return language.lower()

    # Otherwise, look up the ISO code
    return LANGUAGE_TO_ISO.get(language, language.lower())


def get_language_name(iso_code: str) -> str:
    """
    Get language name for an ISO code

    Args:
        iso_code: ISO language code

    Returns:
        Language name or original code if not found
    """
    return ISO_TO_LANGUAGE.get(iso_code.lower(), iso_code)


def download_translated_video(url: str, output_path: str, debug: bool = False) -> bool:
    """
    Download a translated video from HeyGen

    Args:
        url: URL of the translated video
        output_path: Path to save the video
        debug: Whether to print debug information

    Returns:
        True if successful, False otherwise
    """
    try:
        if debug:
            print(f"Downloading translated video from {url} to {output_path}")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if debug:
            print(f"Download completed: {output_path}")

        return True
    except Exception as e:
        if debug:
            print(f"Error downloading translated video: {str(e)}")

        return False

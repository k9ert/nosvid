"""
HeyGen command for nosvid CLI
"""

import os
import time
from datetime import datetime
from .base import get_channel_title
from ...utils.filesystem import setup_directory_structure, get_platform_dir, load_json_file, save_json_file
from ...platforms.youtube import find_youtube_video_file
from ...platforms.heygen import (
    translate_video,
    check_translation_status,
    wait_for_translation,
    download_translated_video,
    get_heygen_metadata,
    update_heygen_metadata,
    list_supported_languages,
    get_iso_code,
    get_language_name
)
from ...utils.config import read_api_key_from_yaml
from ...metadata.common import get_main_metadata, update_main_metadata, update_platform_metadata

def heygen_command(args):
    """
    Translate videos using HeyGen

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        channel_title = get_channel_title()
        print(f"Channel title: {channel_title}")

        # Set up directory structure
        dirs = setup_directory_structure(args.output_dir, channel_title)
        videos_dir = dirs['videos_dir']

        # Load API key
        try:
            api_key = read_api_key_from_yaml('heygen', None)
        except FileNotFoundError:
            print("Error: HeyGen API key not found in config.yaml")
            print("Please add your HeyGen API key to config.yaml:")
            print("heygen:")
            print("  api_key: \"YOUR_HEYGEN_API_KEY\"")
            return 1

        # If list-languages flag is set, just list supported languages and exit
        if args.list_languages:
            print("Fetching supported languages from HeyGen...")
            languages = list_supported_languages(api_key)
            if languages:
                print("\nSupported languages:")
                for i, lang in enumerate(languages, 1):
                    print(f"{i}. {lang}")
                print(f"\nTotal: {len(languages)} languages")
            else:
                print("Failed to fetch supported languages.")
            return 0

        # If no video ID is provided, find the oldest video that hasn't been translated
        video_id = args.video_id
        if not video_id:
            print("No video ID provided. Finding the oldest video that hasn't been translated...")
            # TODO: Implement logic to find the oldest video that hasn't been translated
            print("Automatic selection of videos not yet implemented.")
            print("Please specify a video ID.")
            return 1

        # Get video directory
        video_dir = os.path.join(videos_dir, video_id)
        if not os.path.exists(video_dir):
            print(f"Error: Video directory not found: {video_dir}")
            print("Please sync the video metadata first.")
            return 1

        # Get main metadata
        metadata = get_main_metadata(video_dir)
        if not metadata:
            print(f"Error: Metadata not found for video: {video_id}")
            print("Please sync the video metadata first.")
            return 1

        # Check if the video has been downloaded
        video_file = find_youtube_video_file(video_dir)
        if not video_file and not args.url:
            print(f"Error: Video file not found for ID {video_id}")
            print("Please download the video first or provide a URL with --url.")
            return 1

        # Get video URL (either from YouTube or provided URL)
        video_url = args.url
        if not video_url:
            if 'platforms' in metadata and 'youtube' in metadata['platforms']:
                video_url = metadata['platforms']['youtube']['url']
            else:
                print(f"Error: YouTube URL not found in metadata for ID {video_id}")
                print("Please provide a URL with --url.")
                return 1

        # Get video title
        title = metadata.get('title', f"Video {video_id}")

        # Create platform-specific directory for HeyGen
        heygen_dir = get_platform_dir(video_dir, 'heygen')
        quality_dir = os.path.join(heygen_dir, args.quality)
        os.makedirs(quality_dir, exist_ok=True)

        # Convert language to ISO code
        language = args.language
        iso_code = get_iso_code(language)

        # Check if this video has already been translated in the specified language and quality
        heygen_metadata = get_heygen_metadata(video_dir, args.quality)
        if heygen_metadata and not args.force:
            if 'translations' in heygen_metadata:
                for translation in heygen_metadata['translations']:
                    if translation.get('output_language') == language and translation.get('status') == 'success':
                        print(f"Video already translated to {language} with quality {args.quality}.")
                        print(f"Use --force to retranslate.")
                        return 0

        # Start translation
        print(f"Translating video: {title} ({video_id}) to {language} ({iso_code}) with quality {args.quality}")
        result = translate_video(
            video_url=video_url,
            output_language=language,
            title=title,
            api_key=api_key,
            debug=args.debug
        )

        if not result['success']:
            print(f"Error starting translation: {result.get('error', 'Unknown error')}")
            return 1

        video_translate_id = result['video_translate_id']
        print(f"Translation started. ID: {video_translate_id}")

        # Initialize or update HeyGen metadata
        if not heygen_metadata:
            heygen_metadata = {
                'translations': []
            }

        # Add new translation entry
        translation_entry = {
            'video_translate_id': video_translate_id,
            'output_language': language,
            'language_iso': iso_code,
            'requested_at': result['requested_at'],
            'status': 'pending'
        }

        # Update or add the translation entry
        updated = False
        if 'translations' in heygen_metadata:
            for i, translation in enumerate(heygen_metadata['translations']):
                if translation.get('output_language') == language or translation.get('language_iso') == iso_code:
                    heygen_metadata['translations'][i] = translation_entry
                    updated = True
                    break

        if not updated:
            if 'translations' not in heygen_metadata:
                heygen_metadata['translations'] = []
            heygen_metadata['translations'].append(translation_entry)

        # Save HeyGen metadata
        update_heygen_metadata(video_dir, heygen_metadata, args.quality)

        # Wait for translation to complete if requested
        if args.wait:
            print(f"Waiting for translation to complete (timeout: {args.timeout} seconds)...")
            status = wait_for_translation(
                video_translate_id=video_translate_id,
                api_key=api_key,
                timeout=args.timeout,
                check_interval=args.check_interval,
                debug=args.debug
            )

            if not status['success']:
                print(f"Error during translation: {status.get('error', 'Unknown error')}")

                # Update translation status
                for i, translation in enumerate(heygen_metadata['translations']):
                    if translation.get('video_translate_id') == video_translate_id:
                        heygen_metadata['translations'][i]['status'] = 'failed'
                        heygen_metadata['translations'][i]['error'] = status.get('error', 'Unknown error')
                        heygen_metadata['translations'][i]['checked_at'] = datetime.now().isoformat()
                        break

                update_heygen_metadata(video_dir, heygen_metadata, args.quality)
                return 1

            if status['status'] == 'success':
                print("Translation completed successfully!")

                # Download the translated video if requested
                if args.download:
                    video_url = status['url']
                    output_file = os.path.join(quality_dir, f"{iso_code}.mp4")

                    print(f"Downloading translated video to: {output_file}")
                    download_success = download_translated_video(
                        url=video_url,
                        output_path=output_file,
                        debug=args.debug
                    )

                    if download_success:
                        print(f"Downloaded translated video: {output_file}")
                    else:
                        print("Failed to download translated video.")

                # Update translation status
                for i, translation in enumerate(heygen_metadata['translations']):
                    if translation.get('video_translate_id') == video_translate_id:
                        heygen_metadata['translations'][i]['status'] = 'success'
                        heygen_metadata['translations'][i]['url'] = status.get('url', '')
                        heygen_metadata['translations'][i]['completed_at'] = datetime.now().isoformat()

                        if args.download:
                            heygen_metadata['translations'][i]['local_file'] = output_file

                        break

                update_heygen_metadata(video_dir, heygen_metadata, args.quality)

                # Update main metadata to include HeyGen platform
                if 'platforms' not in metadata:
                    metadata['platforms'] = {}

                if 'heygen' not in metadata['platforms']:
                    metadata['platforms']['heygen'] = {}

                metadata['platforms']['heygen']['translations'] = []
                for translation in heygen_metadata['translations']:
                    if translation.get('status') == 'success':
                        metadata['platforms']['heygen']['translations'].append({
                            'language': translation.get('output_language', ''),
                            'language_iso': translation.get('language_iso', ''),
                            'quality': args.quality,
                            'url': translation.get('url', '')
                        })

                update_main_metadata(video_dir, metadata)

                return 0
            else:
                print(f"Translation not completed within timeout. Current status: {status['status']}")
                return 1
        else:
            print("Translation started in the background.")
            print(f"Check status later with: ./nosvid heygen-status {video_id} --language {args.language} --quality {args.quality}")
            return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


def heygen_status_command(args):
    """
    Check the status of a HeyGen translation

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        channel_title = get_channel_title()
        print(f"Channel title: {channel_title}")

        # Set up directory structure
        dirs = setup_directory_structure(args.output_dir, channel_title)
        videos_dir = dirs['videos_dir']

        # Load API key
        try:
            api_key = read_api_key_from_yaml('heygen', None)
        except FileNotFoundError:
            print("Error: HeyGen API key not found in config.yaml")
            print("Please add your HeyGen API key to config.yaml:")
            print("heygen:")
            print("  api_key: \"YOUR_HEYGEN_API_KEY\"")
            return 1

        # Get video directory
        video_id = args.video_id
        video_dir = os.path.join(videos_dir, video_id)
        if not os.path.exists(video_dir):
            print(f"Error: Video directory not found: {video_dir}")
            return 1

        # Get HeyGen metadata
        heygen_metadata = get_heygen_metadata(video_dir, args.quality)
        if not heygen_metadata or 'translations' not in heygen_metadata:
            print(f"No HeyGen translations found for video: {video_id} with quality: {args.quality}")
            return 1

        # Convert language to ISO code
        language = args.language
        iso_code = get_iso_code(language)

        # Find the translation for the specified language
        translation = None
        for t in heygen_metadata['translations']:
            if t.get('output_language') == language or t.get('language_iso') == iso_code:
                translation = t
                break

        if not translation:
            print(f"No translation found for language: {args.language}")
            return 1

        video_translate_id = translation.get('video_translate_id')
        if not video_translate_id:
            print(f"Error: Translation ID not found for language: {args.language}")
            return 1

        # Check translation status
        print(f"Checking status for translation ID: {video_translate_id}")
        status = check_translation_status(
            video_translate_id=video_translate_id,
            api_key=api_key,
            debug=args.debug
        )

        if not status['success']:
            print(f"Error checking translation status: {status.get('error', 'Unknown error')}")
            return 1

        print(f"Translation status: {status['status']}")

        # Update translation status in metadata
        for i, t in enumerate(heygen_metadata['translations']):
            if t.get('video_translate_id') == video_translate_id:
                heygen_metadata['translations'][i]['status'] = status['status']
                heygen_metadata['translations'][i]['checked_at'] = datetime.now().isoformat()

                if status['status'] == 'success' and 'url' in status:
                    heygen_metadata['translations'][i]['url'] = status['url']
                    heygen_metadata['translations'][i]['completed_at'] = datetime.now().isoformat()

                    # Download the translated video if requested
                    if args.download:
                        quality_dir = os.path.join(get_platform_dir(video_dir, 'heygen'), args.quality)
                        os.makedirs(quality_dir, exist_ok=True)
                        output_file = os.path.join(quality_dir, f"{iso_code}.mp4")

                        print(f"Downloading translated video to: {output_file}")
                        download_success = download_translated_video(
                            url=status['url'],
                            output_path=output_file,
                            debug=args.debug
                        )

                        if download_success:
                            print(f"Downloaded translated video: {output_file}")
                            heygen_metadata['translations'][i]['local_file'] = output_file
                        else:
                            print("Failed to download translated video.")

                break

        update_heygen_metadata(video_dir, heygen_metadata, args.quality)

        # If translation is successful, update main metadata
        if status['status'] == 'success':
            metadata = get_main_metadata(video_dir)

            if 'platforms' not in metadata:
                metadata['platforms'] = {}

            if 'heygen' not in metadata['platforms']:
                metadata['platforms']['heygen'] = {}

            metadata['platforms']['heygen']['translations'] = []
            for t in heygen_metadata['translations']:
                if t.get('status') == 'success':
                    metadata['platforms']['heygen']['translations'].append({
                        'language': t.get('output_language', ''),
                        'language_iso': t.get('language_iso', ''),
                        'quality': args.quality,
                        'url': t.get('url', '')
                    })

            update_main_metadata(video_dir, metadata)

        return 0

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


def register_heygen_parser(subparsers):
    """
    Register the heygen command parser

    Args:
        subparsers: Subparsers object from argparse
    """
    heygen_parser = subparsers.add_parser(
        'heygen',
        help='Translate videos using HeyGen'
    )
    heygen_parser.add_argument(
        'video_id',
        type=str,
        nargs='?',
        help='ID of the video to translate (if not specified, translate the oldest not translated video)'
    )
    heygen_parser.add_argument(
        '--language',
        type=str,
        default='English',
        help='Target language for translation (default: English)'
    )
    heygen_parser.add_argument(
        '--quality',
        type=str,
        default='scale',
        choices=['pro', 'scale'],
        help='Quality level of the translation (default: scale)'
    )
    heygen_parser.add_argument(
        '--url',
        type=str,
        help='URL of the video to translate (if not provided, will use YouTube URL from metadata)'
    )
    heygen_parser.add_argument(
        '--wait',
        action='store_true',
        help='Wait for translation to complete'
    )
    heygen_parser.add_argument(
        '--timeout',
        type=int,
        default=3600,
        help='Maximum time to wait for translation in seconds (default: 3600)'
    )
    heygen_parser.add_argument(
        '--check-interval',
        type=int,
        default=30,
        help='Time between status checks in seconds (default: 30)'
    )
    heygen_parser.add_argument(
        '--download',
        action='store_true',
        help='Download the translated video when complete'
    )
    heygen_parser.add_argument(
        '--force',
        action='store_true',
        help='Force retranslation even if already translated'
    )
    heygen_parser.add_argument(
        '--list-languages',
        action='store_true',
        help='List supported languages and exit'
    )
    heygen_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    # Register heygen-status command
    heygen_status_parser = subparsers.add_parser(
        'heygen-status',
        help='Check the status of a HeyGen translation'
    )
    heygen_status_parser.add_argument(
        'video_id',
        type=str,
        help='ID of the video to check'
    )
    heygen_status_parser.add_argument(
        '--language',
        type=str,
        default='English',
        help='Language of the translation to check (default: English)'
    )
    heygen_status_parser.add_argument(
        '--quality',
        type=str,
        default='scale',
        choices=['pro', 'scale'],
        help='Quality level of the translation (default: scale)'
    )
    heygen_status_parser.add_argument(
        '--download',
        action='store_true',
        help='Download the translated video if complete'
    )
    heygen_status_parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

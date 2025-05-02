"""
Consistency checker for nosvid metadata
"""

import os
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from ..utils.filesystem import setup_directory_structure, load_json_file, save_json_file, get_video_dir
from ..utils.nostr import process_video_directory
from ..metadata.list import generate_metadata_from_files
from .normalizer import normalize_date, normalize_metadata_dates
from .comparator import compare_metadata


class ConsistencyChecker:
    """
    Checks and fixes consistency issues in metadata
    """

    def __init__(self, output_dir: str, channel_title: str, logger: Optional[logging.Logger] = None):
        """
        Initialize the consistency checker

        Args:
            output_dir: Base directory for downloads
            channel_title: Title of the channel
            logger: Logger instance (optional)
        """
        self.output_dir = output_dir
        self.channel_title = channel_title
        self.logger = logger or logging.getLogger(__name__)

        # Set up directory structure
        self.dirs = setup_directory_structure(output_dir, channel_title)
        self.videos_dir = self.dirs['videos_dir']

    def check(self, fix_issues: bool = False) -> Dict[str, Any]:
        """
        Check consistency of metadata.json files for all videos

        Args:
            fix_issues: Whether to fix inconsistencies

        Returns:
            Dictionary with check results
        """
        self.logger.info(f"Checking metadata consistency in {self.output_dir} for channel {self.channel_title}")

        # Ensure videos directory exists
        if not os.path.exists(self.videos_dir):
            self.logger.error(f"Videos directory not found: {self.videos_dir}")
            return self._empty_result()

        # Get all subdirectories (video IDs)
        video_dirs = [d for d in os.listdir(self.videos_dir) if os.path.isdir(os.path.join(self.videos_dir, d))]
        self.logger.info(f"Found {len(video_dirs)} videos in repository")

        # Stage 1: Check each video directory for metadata consistency
        self.logger.info("\nStage 1: Checking metadata consistency for each video directory")
        checked = 0
        inconsistencies = 0
        issues = []

        for video_id in video_dirs:
            video_dir = os.path.join(self.videos_dir, video_id)
            self.logger.info(f"Checking video {checked+1}/{len(video_dirs)}: {video_id}")

            # Check this video
            result = self._check_video(video_dir, video_id, fix_issues)

            # Update counters
            checked += 1
            if result['has_issues']:
                inconsistencies += 1
                issues.append(result['issue'])

            # Print progress
            if checked % 10 == 0 or checked == len(video_dirs):
                self.logger.info(f"Checked {checked}/{len(video_dirs)} videos")

        # Stage 2: Verify video directories against channel_videos JSON files
        self.logger.info("\nStage 2: Verifying video directories against channel_videos JSON files")
        channel_videos_issues = self._verify_against_channel_videos(video_dirs, fix_issues)

        # Add channel_videos issues to the overall issues list
        for issue in channel_videos_issues:
            inconsistencies += 1
            issues.append(issue)

        # Print summary
        self.logger.info("\nConsistency check completed!")
        self.logger.info(f"Total videos: {len(video_dirs)}")
        self.logger.info(f"Videos checked: {checked}")
        self.logger.info(f"Inconsistencies found: {inconsistencies}")

        if inconsistencies > 0:
            self.logger.info("\nInconsistencies:")
            for i, issue in enumerate(issues, 1):
                video_id = issue['video_id']
                issue_type = issue['issue']

                if issue_type == 'missing_metadata':
                    self.logger.info(f"{i}. {video_id}: Missing metadata.json file" +
                                    (" (fixed)" if issue['fixed'] else ""))
                elif issue_type == 'invalid_metadata':
                    self.logger.info(f"{i}. {video_id}: Invalid metadata.json file - {issue['error']}")
                elif issue_type == 'generation_error':
                    self.logger.info(f"{i}. {video_id}: Error generating metadata - {issue['error']}")
                elif issue_type == 'inconsistent_metadata':
                    self.logger.info(f"{i}. {video_id}: Inconsistent metadata - {', '.join(issue['differences'])}" +
                                    (" (fixed)" if issue['fixed'] else ""))
                elif issue_type == 'test_video_directory':
                    self.logger.info(f"{i}. {video_id}: Test video directory - {issue['error']}" +
                                    (" (fixed)" if issue.get('fixed', False) else ""))
                elif issue_type == 'sync_history_only':
                    self.logger.info(f"{i}. {video_id}: In sync_history.json only - {issue['error']}" +
                                    (" (fixed)" if issue.get('fixed', False) else ""))
                elif issue_type == 'invalid_video_directory':
                    self.logger.info(f"{i}. {video_id}: Invalid video directory - {issue['error']}" +
                                    (" (fixed)" if issue.get('fixed', False) else ""))

        return {
            'total': len(video_dirs),
            'checked': checked,
            'inconsistencies': inconsistencies,
            'issues': issues
        }

    def _check_video(self, video_dir: str, video_id: str, fix_issues: bool) -> Dict[str, Any]:
        """
        Check consistency of a single video's metadata

        Args:
            video_dir: Path to the video directory
            video_id: ID of the video
            fix_issues: Whether to fix inconsistencies

        Returns:
            Dictionary with check results for this video
        """
        # Check if metadata.json exists
        metadata_file = os.path.join(video_dir, 'metadata.json')
        if not os.path.exists(metadata_file):
            self.logger.warning(f"No metadata.json found for {video_id}")
            if fix_issues:
                self.logger.info(f"Creating metadata.json for {video_id}...")
                try:
                    generate_metadata_from_files(video_dir, video_id)
                    self.logger.info(f"Created metadata.json for {video_id}")
                except Exception as e:
                    self.logger.error(f"Error creating metadata.json for {video_id}: {e}")

            return {
                'has_issues': True,
                'issue': {
                    'video_id': video_id,
                    'issue': 'missing_metadata',
                    'fixed': fix_issues
                }
            }

        # Load existing metadata
        try:
            existing_metadata = load_json_file(metadata_file)
        except Exception as e:
            self.logger.error(f"Error loading metadata.json for {video_id}: {e}")
            return {
                'has_issues': True,
                'issue': {
                    'video_id': video_id,
                    'issue': 'invalid_metadata',
                    'error': str(e),
                    'fixed': False
                }
            }

        # Generate fresh metadata
        try:
            fresh_metadata = generate_metadata_from_files(video_dir, video_id)

            # Normalize dates in both metadata objects
            existing_metadata = normalize_metadata_dates(existing_metadata)
            fresh_metadata = normalize_metadata_dates(fresh_metadata)
        except Exception as e:
            self.logger.error(f"Error generating fresh metadata for {video_id}: {e}")
            return {
                'has_issues': True,
                'issue': {
                    'video_id': video_id,
                    'issue': 'generation_error',
                    'error': str(e),
                    'fixed': False
                }
            }

        # Process the video directory to extract npubs
        chat_npubs, description_npubs = process_video_directory(video_dir)

        # Add npubs to fresh metadata if found
        if chat_npubs or description_npubs:
            fresh_metadata['npubs'] = {}
            if chat_npubs:
                fresh_metadata['npubs']['chat'] = chat_npubs
            if description_npubs:
                fresh_metadata['npubs']['description'] = description_npubs

        # Check for Nostr posts in platform-specific directories
        fresh_metadata = self._check_for_nostr_posts(video_dir, fresh_metadata)

        # Compare metadata
        differences = compare_metadata(existing_metadata, fresh_metadata)

        if differences:
            self.logger.warning(f"Found {len(differences)} differences for {video_id}")
            for diff in differences:
                self.logger.warning(f"  - {diff}")

            if fix_issues:
                self.logger.info(f"Updating metadata.json for {video_id}...")
                save_json_file(metadata_file, fresh_metadata)
                self.logger.info(f"Updated metadata.json for {video_id}")

            return {
                'has_issues': True,
                'issue': {
                    'video_id': video_id,
                    'issue': 'inconsistent_metadata',
                    'differences': differences,
                    'fixed': fix_issues
                }
            }
        else:
            self.logger.info(f"Metadata for {video_id} is consistent")
            return {
                'has_issues': False
            }

    def _check_for_nostr_posts(self, video_dir: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for Nostr posts in platform-specific directories and add them to the metadata

        Args:
            video_dir: Path to the video directory
            metadata: Metadata dictionary

        Returns:
            Updated metadata dictionary
        """
        # Check if the nostr directory exists
        nostr_dir = os.path.join(video_dir, 'nostr')
        if not os.path.exists(nostr_dir):
            return metadata

        # Initialize platforms dict if it doesn't exist
        if 'platforms' not in metadata:
            metadata['platforms'] = {}

        # Initialize nostr platform if it doesn't exist
        if 'nostr' not in metadata['platforms']:
            metadata['platforms']['nostr'] = {
                'posts': []
            }
        # If using old format (not array-based), convert to new format
        elif 'posts' not in metadata['platforms']['nostr'] and 'event_id' in metadata['platforms']['nostr']:
            # Create a post entry from the existing data
            post_entry = {
                'event_id': metadata['platforms']['nostr']['event_id'],
                'pubkey': metadata['platforms']['nostr'].get('pubkey', ''),
                'nostr_uri': metadata['platforms']['nostr'].get('nostr_uri', ''),
                'links': metadata['platforms']['nostr'].get('links', {}),
                'uploaded_at': metadata['platforms']['nostr'].get('uploaded_at', datetime.now().isoformat())
            }

            # Create the posts array with the single entry
            metadata['platforms']['nostr'] = {
                'posts': [post_entry]
            }

        # Process all nostr metadata files
        self._process_nostr_metadata_files(nostr_dir, metadata)

        # Sort posts by uploaded_at timestamp (newest first)
        if 'nostr' in metadata['platforms'] and 'posts' in metadata['platforms']['nostr']:
            metadata['platforms']['nostr']['posts'].sort(
                key=lambda post: post.get('uploaded_at', ''),
                reverse=True
            )

        return metadata

    def _process_nostr_metadata_files(self, nostr_dir: str, metadata: Dict[str, Any]) -> None:
        """
        Process all nostr metadata files in the nostr directory

        Args:
            nostr_dir: Path to the nostr directory
            metadata: Metadata dictionary to update
        """
        # Check if the nostr metadata file exists
        nostr_metadata_file = os.path.join(nostr_dir, 'metadata.json')
        if os.path.exists(nostr_metadata_file):
            self._process_nostr_metadata_file(nostr_metadata_file, metadata)

        # Check for additional nostr metadata files (for multiple posts)
        for item in os.listdir(nostr_dir):
            # Skip the main metadata.json file
            if item == 'metadata.json':
                continue

            # Check if it's a JSON file
            if not item.endswith('.json'):
                continue

            # Process this additional metadata file
            additional_metadata_file = os.path.join(nostr_dir, item)
            self._process_nostr_metadata_file(additional_metadata_file, metadata, item[:-5])  # Remove .json extension

    def _process_nostr_metadata_file(self, metadata_file: str, metadata: Dict[str, Any],
                                    filename_event_id: str = None) -> None:
        """
        Process a single nostr metadata file

        Args:
            metadata_file: Path to the nostr metadata file
            metadata: Metadata dictionary to update
            filename_event_id: Event ID from the filename (optional)
        """
        try:
            nostr_metadata = load_json_file(metadata_file)

            # Use the event ID from the filename if available, otherwise from the metadata
            event_id = filename_event_id or nostr_metadata.get('event_id')
            if not event_id:
                return

            # Check if the event_id is already in the posts array
            event_exists = False
            for post in metadata['platforms']['nostr'].get('posts', []):
                if post.get('event_id') == event_id:
                    event_exists = True
                    break

            # If the event doesn't exist, add it
            if not event_exists:
                # Create a new post entry
                post_entry = {
                    'event_id': event_id,
                    'pubkey': nostr_metadata.get('pubkey', ''),
                    'nostr_uri': nostr_metadata.get('nostr_uri', ''),
                    'links': nostr_metadata.get('links', {}),
                    'uploaded_at': nostr_metadata.get('uploaded_at', datetime.now().isoformat())
                }

                # Add the new post to the posts array
                metadata['platforms']['nostr']['posts'].append(post_entry)
        except Exception as e:
            self.logger.error(f"Error processing nostr metadata file {metadata_file}: {e}")

    def _verify_against_channel_videos(self, video_dirs: List[str], fix_issues: bool) -> List[Dict[str, Any]]:
        """
        Verify video directories against channel_videos JSON files

        Args:
            video_dirs: List of video directory names (video IDs)
            fix_issues: Whether to fix inconsistencies

        Returns:
            List of issues found
        """
        issues = []

        # Find all channel_videos JSON files
        metadata_dir = self.dirs['metadata_dir']
        channel_videos_files = [f for f in os.listdir(metadata_dir)
                               if f.startswith('channel_videos_') and f.endswith('.json')]

        if not channel_videos_files:
            self.logger.warning("No channel_videos JSON files found")
            return issues

        # Create a set of all video IDs from channel_videos JSON files
        valid_video_ids = set()
        channel_id = None
        channel_videos_data = {}

        for channel_file in channel_videos_files:
            channel_file_path = os.path.join(metadata_dir, channel_file)
            try:
                channel_data = load_json_file(channel_file_path)

                # Store the channel data for later use
                if 'channel_id' in channel_data:
                    channel_id = channel_data['channel_id']
                    channel_videos_data = channel_data

                # Extract video IDs from the channel data
                if 'videos' in channel_data and isinstance(channel_data['videos'], list):
                    for video in channel_data['videos']:
                        if 'video_id' in video:
                            valid_video_ids.add(video['video_id'])
            except Exception as e:
                self.logger.error(f"Error loading channel videos file {channel_file}: {e}")

        self.logger.info(f"Found {len(valid_video_ids)} valid video IDs in channel_videos JSON files")

        # Check for sync_history.json
        sync_history_path = os.path.join(metadata_dir, 'sync_history.json')
        sync_history = {}
        sync_history_ids = set()

        if os.path.exists(sync_history_path):
            try:
                sync_history = load_json_file(sync_history_path)
                for video_id in sync_history:
                    sync_history_ids.add(video_id)
                self.logger.info(f"Found {len(sync_history_ids)} video IDs in sync_history.json")
            except Exception as e:
                self.logger.error(f"Error loading sync_history.json: {e}")

        # Check each video directory against the valid video IDs
        invalid_dirs = []
        test_dirs = []
        sync_history_only_dirs = []

        for video_id in video_dirs:
            if video_id not in valid_video_ids:
                # Check if it's a test directory
                if video_id.startswith('test') or '_test_' in video_id:
                    test_dirs.append(video_id)
                    issues.append({
                        'video_id': video_id,
                        'issue': 'test_video_directory',
                        'error': f"Test video directory not found in any channel_videos JSON file",
                        'fixed': False
                    })
                # Check if it's in sync_history but not in channel_videos
                elif video_id in sync_history_ids:
                    sync_history_only_dirs.append(video_id)
                    issues.append({
                        'video_id': video_id,
                        'issue': 'sync_history_only',
                        'error': f"Video directory found in sync_history.json but not in channel_videos JSON files",
                        'fixed': False
                    })
                else:
                    invalid_dirs.append(video_id)
                    issues.append({
                        'video_id': video_id,
                        'issue': 'invalid_video_directory',
                        'error': f"Video directory not found in any channel_videos JSON file or sync_history.json",
                        'fixed': False
                    })

        # Report findings
        if test_dirs:
            self.logger.warning(f"Found {len(test_dirs)} test video directories:")
            for video_id in test_dirs:
                self.logger.warning(f"  - {video_id}")

        if sync_history_only_dirs:
            self.logger.warning(f"Found {len(sync_history_only_dirs)} directories in sync_history.json but not in channel_videos:")
            for video_id in sync_history_only_dirs:
                self.logger.warning(f"  - {video_id}")

        if invalid_dirs:
            self.logger.warning(f"Found {len(invalid_dirs)} invalid video directories (not in channel_videos or sync_history):")
            for video_id in invalid_dirs:
                self.logger.warning(f"  - {video_id}")

        # Fix issues if requested
        if fix_issues:
            # Only delete test directories and truly invalid directories, not sync_history ones
            dirs_to_delete = test_dirs + invalid_dirs

            if dirs_to_delete:
                self.logger.info(f"Fixing issues by deleting {len(dirs_to_delete)} test/invalid video directories...")
                fixed_count = 0
                for video_id in dirs_to_delete:
                    video_dir = os.path.join(self.videos_dir, video_id)
                    try:
                        # Delete the directory
                        import shutil
                        shutil.rmtree(video_dir)
                        self.logger.info(f"Deleted directory: {video_dir}")

                        # Mark as fixed in the issue
                        for issue in issues:
                            if issue['video_id'] == video_id:
                                issue['fixed'] = True
                                break

                        fixed_count += 1
                    except Exception as e:
                        self.logger.error(f"Error deleting directory {video_dir}: {e}")

                self.logger.info(f"Successfully deleted {fixed_count} out of {len(dirs_to_delete)} directories")

            # Fix sync_history_only directories by adding them to channel_videos
            if sync_history_only_dirs and channel_id:
                self.logger.info(f"Attempting to fix {len(sync_history_only_dirs)} directories found in sync_history.json...")

                # Get the API key from config
                try:
                    from ..utils.config import load_config
                    config = load_config()
                    api_key = config.get('youtube', {}).get('api_key')

                    if not api_key:
                        self.logger.error("No YouTube API key found in config. Cannot fix sync_history discrepancies.")
                    else:
                        # Import the YouTube API functions
                        from ..utils.youtube_api import build_youtube_api

                        # Initialize YouTube API
                        youtube = build_youtube_api(api_key)

                        # Process each video in sync_history_only_dirs
                        fixed_count = 0
                        for video_id in sync_history_only_dirs:
                            try:
                                self.logger.info(f"Fetching metadata for video {video_id} from YouTube API...")

                                # Get video info from sync_history
                                video_info = sync_history.get(video_id, {})

                                # Try to fetch the video directly using the YouTube API
                                request = youtube.videos().list(
                                    part="snippet",
                                    id=video_id
                                )
                                response = request.execute()

                                if response.get('items'):
                                    item = response['items'][0]
                                    snippet = item['snippet']

                                    # Check if this video belongs to the specified channel
                                    if snippet.get('channelId') == channel_id:
                                        # Create video entry
                                        video_entry = {
                                            'title': snippet.get('title', video_info.get('title', f'Video {video_id}')),
                                            'video_id': video_id,
                                            'published_at': snippet.get('publishedAt', video_info.get('published_at', '')),
                                            'url': f"https://www.youtube.com/watch?v={video_id}"
                                        }

                                        # Add to channel_videos data
                                        if 'videos' not in channel_videos_data:
                                            channel_videos_data['videos'] = []

                                        # Check if video already exists
                                        video_exists = False
                                        for video in channel_videos_data['videos']:
                                            if video.get('video_id') == video_id:
                                                video_exists = True
                                                break

                                        if not video_exists:
                                            channel_videos_data['videos'].append(video_entry)

                                            # Mark as fixed in the issue
                                            for issue in issues:
                                                if issue['video_id'] == video_id:
                                                    issue['fixed'] = True
                                                    break

                                            fixed_count += 1
                                            self.logger.info(f"Added video {video_id} to channel_videos_{channel_id}.json")
                                    else:
                                        self.logger.warning(f"Video {video_id} does not belong to channel {channel_id}")
                                else:
                                    self.logger.warning(f"Could not fetch video {video_id} from YouTube API")
                            except Exception as e:
                                self.logger.error(f"Error processing video {video_id}: {e}")

                        # Update channel_videos timestamp and count
                        if fixed_count > 0:
                            channel_videos_data['timestamp'] = datetime.now().isoformat()
                            channel_videos_data['video_count'] = len(channel_videos_data.get('videos', []))

                            # Save updated channel_videos file
                            channel_videos_file = os.path.join(metadata_dir, f"channel_videos_{channel_id}.json")
                            save_json_file(channel_videos_file, channel_videos_data)
                            self.logger.info(f"Successfully added {fixed_count} videos to channel_videos_{channel_id}.json")

                        if fixed_count < len(sync_history_only_dirs):
                            self.logger.info(f"Could not fix {len(sync_history_only_dirs) - fixed_count} videos. "
                                            f"These may require manual intervention.")
                except ImportError:
                    self.logger.error("Could not import required modules to fix sync_history discrepancies.")
                except Exception as e:
                    self.logger.error(f"Error fixing sync_history discrepancies: {e}")
        else:
            if test_dirs or invalid_dirs:
                self.logger.info("To delete test and invalid directories, run with --fix")

            if sync_history_only_dirs:
                self.logger.info("To fix sync_history discrepancies, run with --fix")

        if not (test_dirs or sync_history_only_dirs or invalid_dirs):
            self.logger.info("All video directories are valid and exist in channel_videos JSON files")

        return issues

    def _empty_result(self) -> Dict[str, Any]:
        """
        Create an empty result dictionary

        Returns:
            Empty result dictionary
        """
        return {
            'total': 0,
            'checked': 0,
            'inconsistencies': 0,
            'issues': []
        }

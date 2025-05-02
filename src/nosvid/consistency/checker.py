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

        # Process each video directory
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

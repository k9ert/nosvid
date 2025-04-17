"""
Consistency check functionality for nosvid
"""

import os
import json
import glob
from typing import Dict, Any, List, Tuple
from datetime import datetime

from ..utils.filesystem import setup_directory_structure, load_json_file, save_json_file, get_video_dir
from ..utils.nostr import process_video_directory
from ..metadata.list import generate_metadata_from_files


def check_metadata_consistency(output_dir: str, channel_title: str, fix_issues: bool = False) -> Dict[str, Any]:
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
    videos_dir = dirs['videos_dir']
    if not os.path.exists(videos_dir):
        print(f"Error: Videos directory not found: {videos_dir}")
        return {
            'total': 0,
            'checked': 0,
            'inconsistencies': 0,
            'issues': []
        }
    
    # Get all subdirectories (video IDs)
    video_dirs = [d for d in os.listdir(videos_dir) if os.path.isdir(os.path.join(videos_dir, d))]
    
    print(f"Found {len(video_dirs)} videos in repository")
    
    # Process each video directory
    checked = 0
    inconsistencies = 0
    issues = []
    
    for video_id in video_dirs:
        video_dir = os.path.join(videos_dir, video_id)
        print(f"Checking video {checked+1}/{len(video_dirs)}: {video_id}", end="", flush=True)
        
        # Check if metadata.json exists
        metadata_file = os.path.join(video_dir, 'metadata.json')
        if not os.path.exists(metadata_file):
            print(f" - No metadata.json found")
            if fix_issues:
                print(f"  Creating metadata.json...")
                generate_metadata_from_files(video_dir, video_id)
                print(f"  Created metadata.json")
            
            issues.append({
                'video_id': video_id,
                'issue': 'missing_metadata',
                'fixed': fix_issues
            })
            inconsistencies += 1
            checked += 1
            continue
        
        # Load existing metadata
        try:
            existing_metadata = load_json_file(metadata_file)
        except Exception as e:
            print(f" - Error loading metadata.json: {e}")
            issues.append({
                'video_id': video_id,
                'issue': 'invalid_metadata',
                'error': str(e),
                'fixed': False
            })
            inconsistencies += 1
            checked += 1
            continue
        
        # Generate fresh metadata
        try:
            fresh_metadata = generate_metadata_from_files(video_dir, video_id)
        except Exception as e:
            print(f" - Error generating fresh metadata: {e}")
            issues.append({
                'video_id': video_id,
                'issue': 'generation_error',
                'error': str(e),
                'fixed': False
            })
            inconsistencies += 1
            checked += 1
            continue
        
        # Process the video directory to extract npubs
        chat_npubs, description_npubs = process_video_directory(video_dir)
        
        # Add npubs to fresh metadata if found
        if chat_npubs or description_npubs:
            fresh_metadata['npubs'] = {}
            if chat_npubs:
                fresh_metadata['npubs']['chat'] = chat_npubs
            if description_npubs:
                fresh_metadata['npubs']['description'] = description_npubs
        
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
            
            issues.append({
                'video_id': video_id,
                'issue': 'inconsistent_metadata',
                'differences': differences,
                'fixed': fix_issues
            })
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
            video_id = issue['video_id']
            issue_type = issue['issue']
            
            if issue_type == 'missing_metadata':
                print(f"{i}. {video_id}: Missing metadata.json file" + (" (fixed)" if issue['fixed'] else ""))
            elif issue_type == 'invalid_metadata':
                print(f"{i}. {video_id}: Invalid metadata.json file - {issue['error']}")
            elif issue_type == 'generation_error':
                print(f"{i}. {video_id}: Error generating metadata - {issue['error']}")
            elif issue_type == 'inconsistent_metadata':
                print(f"{i}. {video_id}: Inconsistent metadata - {', '.join(issue['differences'])}" + 
                      (" (fixed)" if issue['fixed'] else ""))
    
    return {
        'total': len(video_dirs),
        'checked': checked,
        'inconsistencies': inconsistencies,
        'issues': issues
    }


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
    for field in ['title', 'video_id', 'published_at', 'duration']:
        if field in fresh and (field not in existing or existing[field] != fresh[field]):
            differences.append(f"Different {field}")
    
    # Check platforms
    if 'platforms' in fresh:
        if 'platforms' not in existing:
            differences.append("Missing platforms section")
        else:
            # Check YouTube platform
            if 'youtube' in fresh['platforms']:
                if 'youtube' not in existing['platforms']:
                    differences.append("Missing YouTube platform")
                else:
                    # Check YouTube URL
                    if 'url' in fresh['platforms']['youtube'] and (
                            'url' not in existing['platforms']['youtube'] or 
                            existing['platforms']['youtube']['url'] != fresh['platforms']['youtube']['url']):
                        differences.append("Different YouTube URL")
                    
                    # Check YouTube download status
                    if 'downloaded' in fresh['platforms']['youtube'] and (
                            'downloaded' not in existing['platforms']['youtube'] or 
                            existing['platforms']['youtube']['downloaded'] != fresh['platforms']['youtube']['downloaded']):
                        differences.append("Different YouTube download status")
            
            # Check nostrmedia platform
            if 'nostrmedia' in fresh['platforms']:
                if 'nostrmedia' not in existing['platforms']:
                    differences.append("Missing nostrmedia platform")
                else:
                    # Check nostrmedia URL
                    if 'url' in fresh['platforms']['nostrmedia'] and (
                            'url' not in existing['platforms']['nostrmedia'] or 
                            existing['platforms']['nostrmedia']['url'] != fresh['platforms']['nostrmedia']['url']):
                        differences.append("Different nostrmedia URL")
    
    # Check npubs
    if 'npubs' in fresh:
        if 'npubs' not in existing:
            differences.append("Missing npubs section")
        else:
            # Check chat npubs
            if 'chat' in fresh['npubs']:
                if 'chat' not in existing['npubs']:
                    differences.append("Missing chat npubs")
                elif set(fresh['npubs']['chat']) != set(existing['npubs']['chat']):
                    differences.append("Different chat npubs")
            
            # Check description npubs
            if 'description' in fresh['npubs']:
                if 'description' not in existing['npubs']:
                    differences.append("Missing description npubs")
                elif set(fresh['npubs']['description']) != set(existing['npubs']['description']):
                    differences.append("Different description npubs")
    elif 'npubs' in existing:
        differences.append("Extra npubs section in existing metadata")
    
    return differences

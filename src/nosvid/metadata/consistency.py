"""
Backward compatibility module for consistency checking
"""

import logging
from typing import Any, Dict

from ..consistency import ConsistencyChecker


def check_metadata_consistency(
    output_dir: str, channel_title: str, fix_issues: bool = False
) -> Dict[str, Any]:
    """
    Check consistency of metadata.json files for all videos (backward compatibility function)

    Args:
        output_dir: Base directory for downloads
        channel_title: Title of the channel
        fix_issues: Whether to fix inconsistencies

    Returns:
        Dictionary with check results
    """
    # Configure logging
    logger = logging.getLogger("nosvid.consistency")

    # Create and run the consistency checker
    checker = ConsistencyChecker(output_dir, channel_title, logger)
    return checker.check(fix_issues=fix_issues)

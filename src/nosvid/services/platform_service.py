"""
Platform service for nosvid

This service manages platform activation and provides methods to check if a platform is activated.
"""

from typing import Dict, Optional

from ..utils.config import load_config


class PlatformService:
    """
    Service for platform operations
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the service

        Args:
            config: Configuration dictionary (optional, will load from config.yaml if not provided)
        """
        self.config = config or load_config()

    def is_platform_activated(self, platform_name: str) -> bool:
        """
        Check if a platform is activated

        Args:
            platform_name: Name of the platform (e.g., 'youtube', 'nostrmedia', 'nostr')

        Returns:
            True if the platform is activated, False otherwise
        """
        # Check if the platform section exists in the config
        if platform_name not in self.config:
            return False

        # Check if the platform has an 'activated' key
        if "activated" not in self.config[platform_name]:
            return False

        # Return the activation status
        return self.config[platform_name]["activated"]

    def check_platform_activated(self, platform_name: str) -> None:
        """
        Check if a platform is activated and raise an exception if not

        Args:
            platform_name: Name of the platform (e.g., 'youtube', 'nostrmedia', 'nostr')

        Raises:
            ValueError: If the platform is not activated
        """
        # Import the appropriate platform module based on the platform name
        if platform_name == "youtube":
            from ..platforms.youtube import check_platform_activated
        elif platform_name == "nostrmedia":
            from ..platforms.nostrmedia import check_platform_activated
        elif platform_name == "nostr":
            from ..platforms.nostr import check_platform_activated
        else:
            # For unknown platforms, use the default check
            if not self.is_platform_activated(platform_name):
                raise ValueError(
                    f"Platform '{platform_name}' is not activated. "
                    f"Please activate it in your config.yaml file by setting {platform_name}.activated = true"
                )
            return

        # Call the platform-specific check
        check_platform_activated()

    def get_platform_config(self, platform_name: str) -> Dict:
        """
        Get the configuration for a platform

        Args:
            platform_name: Name of the platform (e.g., 'youtube', 'nostrmedia', 'nostr')

        Returns:
            Platform configuration dictionary
        """
        # Check if the platform is activated
        self.check_platform_activated(platform_name)

        # Return the platform configuration
        return self.config.get(platform_name, {})

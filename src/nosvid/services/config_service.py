"""
Configuration service for nosvid
"""

import os
from typing import Any, Dict, Optional

import yaml


class ConfigService:
    """
    Service for configuration operations
    """

    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize the service

        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file

        Returns:
            Configuration dictionary
        """
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value

        Args:
            key: Configuration key (dot-separated for nested keys)
            default: Default value if key is not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value

        Args:
            key: Configuration key (dot-separated for nested keys)
            value: Configuration value
        """
        keys = key.split(".")
        config = self.config

        # Handle simple case
        if len(keys) == 1:
            config[keys[0]] = value
            return

        # Handle nested case
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self) -> None:
        """
        Save configuration to file
        """
        with open(self.config_file, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a service

        Args:
            service: Service name

        Returns:
            API key or None if not found
        """
        return self.get(f"{service}.api_key")

    def get_nostr_key(self, key_type: str) -> Optional[str]:
        """
        Get Nostr key (nsec or npub)

        Args:
            key_type: Key type ('nsec' or 'npub')

        Returns:
            Nostr key or None if not found
        """
        return self.get(f"nostr.{key_type}")

    def get_output_dir(self) -> str:
        """
        Get output directory

        Returns:
            Output directory
        """
        output_dir = self.get("defaults.output_dir")
        if output_dir is None:
            return "./repository"
        return output_dir

    def get_channel_title(self) -> str:
        """
        Get channel title

        Returns:
            Channel title
        """
        channel_title = self.get("channel.title")
        if channel_title is None:
            return "Einundzwanzig"
        return channel_title

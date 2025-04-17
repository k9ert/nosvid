"""
Configuration utilities for nosvid
"""

import os
import yaml

def load_config(config_path='config.yaml'):
    """
    Load configuration from YAML file

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    # Try to load from config.yaml
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except (FileNotFoundError, yaml.YAMLError):
        # Return empty config if file not found or invalid
        return {}

def read_api_key_from_yaml(service_name, key_name=None):
    """
    Read API key from YAML file

    Args:
        service_name: Name of the service (e.g., 'youtube')
        key_name: Name of the key file (e.g., 'youtube.key')

    Returns:
        API key as string
    """
    # Try to read from config.yaml first
    try:
        config = load_config()
        if service_name in config and 'api_key' in config[service_name]:
            return config[service_name]['api_key']
    except Exception:
        pass

    # Try to read from secrets.yaml for backward compatibility
    try:
        with open('secrets.yaml', 'r') as f:
            secrets = yaml.safe_load(f)
            if service_name in secrets and 'api_key' in secrets[service_name]:
                return secrets[service_name]['api_key']
    except (FileNotFoundError, yaml.YAMLError):
        pass

    # If not found, try to read from key file for backward compatibility
    if key_name:
        try:
            with open(key_name, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            pass

    # If still not found, try environment variable
    env_var_name = f"{service_name.upper()}_API_KEY"
    if env_var_name in os.environ:
        return os.environ[env_var_name]

    raise FileNotFoundError(f"Could not find API key for {service_name}")

def get_nostr_key(key_type):
    """
    Get Nostr key from configuration

    Args:
        key_type: Type of key to retrieve ('nsec' or 'npub')

    Returns:
        Key as string or None if not found
    """
    config = load_config()
    if 'nostr' in config and key_type in config['nostr']:
        return config['nostr'][key_type]
    return None

def get_default_output_dir():
    """
    Get the default output directory for downloads

    Returns:
        Default output directory path
    """
    config = load_config()
    if 'defaults' in config and 'output_dir' in config['defaults']:
        return os.path.expanduser(config['defaults']['output_dir'])
    return os.path.expanduser("~/Downloads/nosvid")

def get_default_video_quality():
    """
    Get the default video quality

    Returns:
        Default video quality
    """
    config = load_config()
    if 'defaults' in config and 'video_quality' in config['defaults']:
        return config['defaults']['video_quality']
    return 'best'

def get_default_download_delay():
    """
    Get the default download delay

    Returns:
        Default download delay in seconds
    """
    config = load_config()
    if 'defaults' in config and 'download_delay' in config['defaults']:
        return config['defaults']['download_delay']
    return 5

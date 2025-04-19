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

def get_nostr_relays():
    """
    Get Nostr relays from configuration

    Returns:
        List of relay URLs or None if not found
    """
    config = load_config()
    if 'nostr' in config and 'relays' in config['nostr']:
        return config['nostr']['relays']

    # Default relays if not specified in config
    return [
        # Primary relays
        "wss://relay.damus.io",        # Damus relay (very popular)
        "wss://nos.lol",              # nos.lol (very reliable)
        "wss://nostr.wine",           # nostr.wine (popular for media)
        "wss://relay.nostr.band",     # nostr.band (search indexer)
        "wss://relay.snort.social",   # Snort relay (popular client)
        "wss://purplepag.es",         # Purple Pages (directory)

        # Secondary relays
        "wss://nostr.mutinywallet.com", # Mutiny wallet relay
        "wss://relay.nostrudel.ninja",  # Nostrudel relay
        "wss://relay.primal.net"        # Primal relay
    ]

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

def get_default_web_port():
    """
    Get the default web port

    Returns:
        Default web port
    """
    config = load_config()
    if 'defaults' in config and 'web_port' in config['defaults']:
        return config['defaults']['web_port']
    return 2121

def get_youtube_cookies_file():
    """
    Get the YouTube cookies file path from config

    Returns:
        Path to cookies file or None if not configured
    """
    config = load_config()
    if 'youtube' in config and 'cookies_file' in config['youtube']:
        return os.path.expanduser(config['youtube']['cookies_file'])
    return None

def get_channel_id():
    """
    Get the channel ID for Einundzwanzig

    Returns:
        Channel ID for Einundzwanzig
    """
    # Hardcoded channel ID for Einundzwanzig
    return "UCxSRxq14XIoMbFDEjMOPU5Q"

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

def get_youtube_api_key():
    """
    Get the YouTube API key from config

    Returns:
        YouTube API key or None if not configured
    """
    config = load_config()
    if 'youtube' in config and 'api_key' in config['youtube']:
        return config['youtube']['api_key']
    return None

def get_repository_dir():
    """
    Get the repository directory from config

    Returns:
        Repository directory or './repository' if not configured
    """
    config = load_config()
    if 'defaults' in config and 'repository_dir' in config['defaults']:
        return config['defaults']['repository_dir']
    return './repository'

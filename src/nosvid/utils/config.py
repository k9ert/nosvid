"""
Configuration utilities for nosvid
"""

import os
import yaml

def read_api_key_from_yaml(service_name, key_name=None):
    """
    Read API key from YAML file
    
    Args:
        service_name: Name of the service (e.g., 'youtube')
        key_name: Name of the key file (e.g., 'youtube.key')
        
    Returns:
        API key as string
    """
    # Try to read from secrets.yaml first
    try:
        with open('secrets.yaml', 'r') as f:
            secrets = yaml.safe_load(f)
            if service_name in secrets and 'api_key' in secrets[service_name]:
                return secrets[service_name]['api_key']
    except (FileNotFoundError, yaml.YAMLError):
        pass
    
    # If not found, try to read from key file
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

def get_default_output_dir():
    """
    Get the default output directory for downloads
    
    Returns:
        Default output directory path
    """
    return os.path.expanduser("~/Downloads/nosvid")

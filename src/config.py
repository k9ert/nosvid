import yaml
import os

def read_api_key_from_yaml(key_name, file_path=None):
    """
    Reads the specified key from a file. Supports both YAML and plain text files.

    Args:
    key_name (str): The key to retrieve from the YAML file. Ignored for plain text files.
    file_path (str, optional): Path to the file. If None, will try common locations.

    Returns:
    str: The API key

    Raises:
    FileNotFoundError: If the file is not found
    KeyError: If the key is not found in YAML file
    """
    if file_path is None:
        # Try common locations
        common_paths = ['secrets.yaml', 'youtube.key']
        for path in common_paths:
            if os.path.exists(path):
                file_path = path
                break
        if file_path is None:
            raise FileNotFoundError("No API key file found in common locations")

    try:
        with open(file_path, 'r') as f:
            if file_path.endswith('.yaml'):
                data = yaml.safe_load(f)
                return data[key_name]
            else:
                return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"API key file not found: {file_path}")
    except KeyError:
        raise KeyError(f"Key '{key_name}' not found in {file_path}")
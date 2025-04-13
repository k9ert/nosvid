"""
Upload functionality for nostrmedia.com
"""

import os
import time
import hashlib
import requests
import base64
import json
from datetime import datetime
from nostr.key import PrivateKey
from nostr.event import Event
from nostr.event import EventKind

def compute_sha256(file_path):
    """
    Compute the SHA-256 hash of a file

    Args:
        file_path: Path to the file

    Returns:
        SHA-256 hash as a hex string
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read the file in chunks to avoid loading large files into memory
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()

def create_signed_event(private_key, file_hash):
    """
    Create a signed Nostr event for uploading to nostrmedia.com

    Args:
        private_key: Nostr private key
        file_hash: SHA-256 hash of the file

    Returns:
        Signed Nostr event
    """
    # Create a custom event with kind 24242
    event = Event(
        content="Uploading blob with SHA-256 hash",
        kind=24242,
        created_at=int(time.time())
    )

    # Add required tags
    event.tags.append(["t", "upload"])
    event.tags.append(["x", file_hash])

    # Sign the event
    private_key.sign_event(event)

    return event

def upload_to_nostrmedia(file_path, private_key_str=None):
    """
    Upload a file to nostrmedia.com

    Args:
        file_path: Path to the file to upload
        private_key_str: Private key string (hex or nsec format, if None, a new key will be generated)

    Returns:
        Dictionary with upload result
    """
    if not os.path.exists(file_path):
        return {
            'success': False,
            'error': f"File not found: {file_path}"
        }

    try:
        # Compute the SHA-256 hash of the file
        file_hash = compute_sha256(file_path)
        print(f"File hash: {file_hash}")

        # Create or load private key
        if private_key_str:
            try:
                # Check if it's a bech32-encoded key (starts with 'nsec')
                if private_key_str.startswith('nsec'):
                    private_key = PrivateKey.from_nsec(private_key_str)
                # Otherwise, assume it's a hex string
                else:
                    private_key = PrivateKey(bytes.fromhex(private_key_str))
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Invalid private key format: {str(e)}"
                }
        else:
            private_key = PrivateKey()

        # Create and sign the event
        event = create_signed_event(private_key, file_hash)

        # Encode the event as JSON and then as base64
        event_json = json.dumps(event.to_json_object())
        event_base64 = base64.b64encode(event_json.encode()).decode()

        # Prepare the upload request
        url = "https://nostrmedia.com/upload"
        headers = {
            "Authorization": f"Nostr {event_base64}"
        }

        # Open the file for upload
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, "application/octet-stream")
            }

            # Send the upload request
            print(f"Uploading file to {url}...")
            response = requests.post(url, headers=headers, files=files)

            if response.status_code == 200:
                print("Upload successful!")
                return {
                    'success': True,
                    'url': f"https://nostrmedia.com/{file_hash}",
                    'hash': file_hash,
                    'response': response.json() if response.content else {}
                }
            else:
                print(f"Upload failed with status code {response.status_code}")
                return {
                    'success': False,
                    'error': f"Upload failed with status code {response.status_code}",
                    'response': response.text
                }

    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

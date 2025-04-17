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
from ..utils.config import get_nostr_key

# Try to import nostr-sdk packages, but make them optional
try:
    from nostr_sdk import Keys, EventBuilder, Tag, Kind, Event, NostrSigner
    NOSTR_AVAILABLE = True
except ImportError:
    NOSTR_AVAILABLE = False
    print("Warning: nostr-sdk package not available. Nostrmedia upload functionality will be limited.")

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

def create_signed_event(keys, file_hash, file_path=None, debug=False):
    """
    Create a signed Nostr event for uploading to nostrmedia.com

    Args:
        keys: Nostr Keys object
        file_hash: SHA-256 hash of the file
        file_path: Path to the file (for extension info)
        debug: Whether to print debug information

    Returns:
        Signed Nostr event
    """
    import asyncio

    # Get file extension if file_path is provided
    file_ext = None
    if file_path:
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext and file_ext.startswith('.'):
            file_ext = file_ext[1:]  # Remove the leading dot

    if debug:
        print("\n=== DEBUG: Event Creation ===")
        print(f"Public key: {keys.public_key().to_hex()}")
        print(f"File hash: {file_hash}")
        print(f"File extension: {file_ext if file_ext else 'None'}")
        print(f"Event kind: 24242 (custom for nostrmedia)")

    # Create a custom event with kind 24242
    kind = Kind(24242)
    builder = EventBuilder(kind, "Uploading blob with SHA-256 hash")

    # Add tags
    t_tag = Tag.parse(["t", "upload"])
    x_tag = Tag.parse(["x", file_hash])
    tags = [t_tag, x_tag]

    # Add file extension tag if available
    if file_ext:
        ext_tag = Tag.parse(["ext", file_ext])
        tags.append(ext_tag)
        if debug:
            print(f"Added extension tag: {ext_tag.as_vec()}")

    builder = builder.tags(tags)

    if debug:
        print("\n=== DEBUG: Event Tags ===")
        print(f"t tag: {t_tag.as_vec()}")
        print(f"x tag: {x_tag.as_vec()}")

    # Create a signer from keys
    signer = NostrSigner.keys(keys)

    if debug:
        print("\n=== DEBUG: Signer Created ===")
        print(f"Signer type: NostrSigner with Keys")

    # Set up the event loop for async operations
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # If there's no event loop in the current thread, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if debug:
        print("\n=== DEBUG: Signing Event ===")

    # Sign the event (this is an async operation in Python)
    event = loop.run_until_complete(builder.sign(signer))

    if debug:
        print("Event signed successfully")
        print(f"Event ID: {event.id().to_hex()}")
        # The signature is part of the JSON representation, not directly accessible

    return event

def upload_to_nostrmedia(file_path, private_key_str=None, debug=False):
    """
    Upload a file to nostrmedia.com

    Args:
        file_path: Path to the file to upload
        private_key_str: Private key string (hex or nsec format, if None, will try to use from config)
        debug: Whether to print detailed debug information

    Returns:
        Dictionary with upload result
    """
    if not NOSTR_AVAILABLE:
        return {
            'success': False,
            'error': "nostr-sdk package not available. Please install it with 'pip install nostr-sdk'"
        }

    if not os.path.exists(file_path):
        return {
            'success': False,
            'error': f"File not found: {file_path}"
        }

    try:
        # Compute the SHA-256 hash of the file
        file_hash = compute_sha256(file_path)
        print(f"File hash: {file_hash}")

        if debug:
            print("\n=== DEBUG: Upload Parameters ===")
            print(f"File path: {file_path}")
            print(f"File size: {os.path.getsize(file_path)} bytes")
            print(f"File hash: {file_hash}")
            print(f"Private key provided: {bool(private_key_str)}")

        # Create or load keys
        if private_key_str:
            # Use the provided private key
            try:
                # Parse the private key (works with both hex and bech32/nsec format)
                keys = Keys.parse(private_key_str)
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Invalid private key format: {str(e)}"
                }
        else:
            # Try to get the private key from config
            config_nsec = get_nostr_key('nsec')

            if debug and config_nsec:
                print("\n=== DEBUG: Config Key ===")
                print(f"Config nsec format: {config_nsec[:4]}...{config_nsec[-4:] if len(config_nsec) > 8 else ''}")

            if config_nsec:
                try:
                    keys = Keys.parse(config_nsec)
                    print("Using private key from config.yaml")
                except Exception as e:
                    print(f"Warning: Invalid private key in config: {str(e)}")
                    print("Generating a new private key instead")
                    keys = Keys.generate()
            else:
                # If no key is provided or found in config, generate a new one
                print("No private key provided or found in config. Generating a new one.")
                keys = Keys.generate()

        # Create and sign the event
        event = create_signed_event(keys, file_hash, file_path=file_path, debug=debug)

        # Get the event as JSON and encode it as base64
        event_json = event.as_json()
        print(f"Event JSON: {event_json}")
        event_base64 = base64.b64encode(event_json.encode()).decode()

        if debug:
            print("\n=== DEBUG: Event Encoding ===")
            print(f"Event JSON length: {len(event_json)} bytes")
            print(f"Event Base64 length: {len(event_base64)} bytes")

        # Prepare the upload request
        url = "https://nostrmedia.com/upload"
        headers = {
            "Authorization": f"Nostr {event_base64}"
        }

        if debug:
            print("\n=== DEBUG: Upload Request ===")
            print(f"URL: {url}")
            print(f"Headers: {headers}")

        # Determine the MIME type based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        mime_type = "application/octet-stream"  # Default MIME type

        # Map common video extensions to MIME types
        mime_types = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".mkv": "video/x-matroska",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".wmv": "video/x-ms-wmv",
            ".flv": "video/x-flv"
        }

        if file_ext in mime_types:
            mime_type = mime_types[file_ext]

        if debug:
            print(f"\n=== DEBUG: File Type ===\nFile extension: {file_ext}\nMIME type: {mime_type}")

        # Open the file for upload
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, mime_type)
            }

            # Send the upload request
            print(f"Uploading file to {url}...")

            if debug:
                print("\n=== DEBUG: File Upload ===")
                print(f"File name: {os.path.basename(file_path)}")
                print(f"Content type: {mime_type}")

            response = requests.post(url, headers=headers, files=files)

            if debug:
                print("\n=== DEBUG: Response ===")
                print(f"Status code: {response.status_code}")
                print(f"Response headers: {response.headers}")
                print(f"Response content: {response.text[:500]}{'...' if len(response.text) > 500 else ''}")

            if response.status_code == 200:
                print("Upload successful!")

                # Parse the response to get the actual URL
                response_data = response.json() if response.content else {}
                url = response_data.get('url', f"https://nostrmedia.com/{file_hash}")

                if debug:
                    print(f"\n=== DEBUG: URL Handling ===")
                    print(f"Response URL: {url}")
                    print(f"File hash: {file_hash}")

                return {
                    'success': True,
                    'url': url,
                    'hash': file_hash,
                    'response': response_data
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

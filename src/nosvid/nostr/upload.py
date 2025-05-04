"""
Functions for uploading videos to the Nostr network
"""

import json
import os
import time
from datetime import datetime

try:
    print("Attempting to import nostr_sdk...")
    from nostr_sdk import (
        Client,
        EventBuilder,
        Keys,
        Kind,
        NostrSigner,
        RelayOptions,
        Tag,
    )

    print("nostr_sdk imported successfully")
    NOSTR_AVAILABLE = True
except ImportError as e:
    print(f"ImportError: {e}")
    NOSTR_AVAILABLE = False
    print(
        "Warning: nostr-sdk package not available. Nostr upload functionality will be limited."
    )

import os.path

from ..nostrmedia.upload import upload_to_nostrmedia
from ..utils.config import get_nostr_key, get_nostr_relays, load_config
from ..utils.filesystem import (
    get_platform_dir,
    get_video_dir,
    load_json_file,
    save_json_file,
)


def post_to_nostr(video_id, channel_id, debug=False):
    """
    Post a video to Nostr, handling all the necessary steps

    Args:
        video_id: YouTube video ID
        channel_id: Channel ID
        debug: Whether to print debug information

    Returns:
        True if successful, False otherwise
    """
    try:
        if debug:
            print(f"Posting video {video_id} to Nostr")

        # Get the video directory
        video_dir = os.path.join(get_video_dir(channel_id), video_id)

        # Check if the video exists
        if not os.path.exists(video_dir):
            print(f"Video directory not found: {video_dir}")
            return False

        # Load the metadata
        metadata_path = os.path.join(video_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            print(f"Metadata file not found: {metadata_path}")
            return False

        metadata = load_json_file(metadata_path)

        # Check if the video has been downloaded
        youtube_dir = os.path.join(video_dir, "youtube")
        video_files = (
            [f for f in os.listdir(youtube_dir) if f.endswith(".mp4")]
            if os.path.exists(youtube_dir)
            else []
        )

        if not video_files:
            print(f"No video files found in {youtube_dir}")
            print("Downloading video first...")
            from ..download.video import download_video

            download_result = download_video(video_id, channel_id)
            if not download_result:
                print("Failed to download video")
                return False

            # Refresh the list of video files
            video_files = [f for f in os.listdir(youtube_dir) if f.endswith(".mp4")]

        # Get the video file path
        video_file = video_files[0] if video_files else None
        if not video_file:
            print("No video file found after download attempt")
            return False

        video_path = os.path.join(youtube_dir, video_file)

        # Check if the video has been uploaded to nostrmedia
        nostrmedia_url = None
        if (
            "platforms" in metadata
            and "nostrmedia" in metadata["platforms"]
            and "url" in metadata["platforms"]["nostrmedia"]
        ):
            nostrmedia_url = metadata["platforms"]["nostrmedia"]["url"]

        if not nostrmedia_url:
            print("Video not uploaded to nostrmedia yet")
            print("Uploading to nostrmedia first...")

            # Upload to nostrmedia
            nostrmedia_result = upload_to_nostrmedia(video_id, channel_id, debug=debug)
            if not nostrmedia_result or not nostrmedia_result.get("success"):
                print("Failed to upload to nostrmedia")
                return False

            # Get the nostrmedia URL
            nostrmedia_url = nostrmedia_result.get("url")
            if not nostrmedia_url:
                print("No nostrmedia URL returned")
                return False

            # Update the metadata
            metadata["platforms"] = metadata.get("platforms", {})
            metadata["platforms"]["nostrmedia"] = {
                "url": nostrmedia_url,
                "uploaded_at": datetime.now().isoformat(),
            }
            save_json_file(metadata_path, metadata)

        # Prepare metadata for nostr
        nostr_metadata = {
            "title": metadata.get("title", ""),
            "full_description": metadata.get("description", ""),
            "published_at": metadata.get("published_at", ""),
            "channel_title": metadata.get("channel_title", ""),
            "video_id": video_id,
            "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
            "nostrmedia_url": nostrmedia_url,
        }

        # Upload to nostr
        nostr_result = upload_to_nostr(video_path, nostr_metadata, debug=debug)
        if not nostr_result or not nostr_result.get("success"):
            print(
                f"Failed to upload to nostr: {nostr_result.get('error') if nostr_result else 'Unknown error'}"
            )
            return False

        # Update the metadata with nostr information
        nostr_dir = os.path.join(video_dir, "nostr")
        os.makedirs(nostr_dir, exist_ok=True)

        # Create or update the nostr metadata file
        nostr_metadata_path = os.path.join(nostr_dir, "metadata.json")
        nostr_metadata = (
            load_json_file(nostr_metadata_path)
            if os.path.exists(nostr_metadata_path)
            else {}
        )

        # Add the new post to the posts array
        nostr_metadata["posts"] = nostr_metadata.get("posts", [])
        nostr_metadata["posts"].append(
            {
                "event_id": nostr_result.get("event_id"),
                "pubkey": nostr_result.get("pubkey"),
                "uploaded_at": datetime.now().isoformat(),
                "nostr_uri": nostr_result.get("nostr_uri"),
                "links": nostr_result.get("links", {}),
            }
        )

        # Save the nostr metadata
        save_json_file(nostr_metadata_path, nostr_metadata)

        # Update the main metadata file
        metadata["platforms"] = metadata.get("platforms", {})
        metadata["platforms"]["nostr"] = {"posts": nostr_metadata["posts"]}
        save_json_file(metadata_path, metadata)

        print(f"Successfully posted video {video_id} to Nostr")
        return True

    except Exception as e:
        print(f"Error posting to Nostr: {str(e)}")
        return False


def upload_to_nostr(file_path, metadata, private_key_str=None, debug=False):
    """
    Upload a video to the Nostr network

    Args:
        file_path: Path to the video file
        metadata: Dictionary containing video metadata
        private_key_str: Private key string (hex or nsec format, if None, will try to use from config)
        debug: Whether to print detailed debug information

    Returns:
        Dictionary with upload result
    """
    if not NOSTR_AVAILABLE:
        return {
            "success": False,
            "error": "nostr-sdk package not available. Please install it with 'pip install nostr-sdk'",
        }

    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    try:
        # Get file information
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()

        if debug:
            print("\n=== DEBUG: File Information ===")
            print(f"File path: {file_path}")
            print(f"File name: {file_name}")
            print(f"File size: {file_size} bytes")
            print(f"File extension: {file_ext}")

        # Create or load keys
        if private_key_str:
            # Use the provided private key
            try:
                keys = Keys.parse(private_key_str)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Invalid private key format: {str(e)}",
                }
        else:
            # Try to get the private key from config
            config_nsec = get_nostr_key("nsec")

            if debug and config_nsec:
                print("\n=== DEBUG: Config Key ===")
                print(
                    f"Config nsec format: {config_nsec[:4]}...{config_nsec[-4:] if len(config_nsec) > 8 else ''}"
                )

            if config_nsec:
                try:
                    keys = Keys.parse(config_nsec)
                    print("Using private key from config.yaml")
                except Exception as e:
                    print(f"Warning: Invalid private key in config: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Invalid nsec key in config.yaml: {str(e)}",
                    }
            else:
                return {
                    "success": False,
                    "error": "No private key provided or found in config.",
                }

        # Extract relevant metadata
        title = metadata.get("title", "Untitled Video")
        description = metadata.get("full_description", metadata.get("description", ""))
        published_at = metadata.get("published_at", "")
        channel_title = metadata.get("channel_title", "")
        video_id = metadata.get("video_id", "")
        youtube_url = metadata.get(
            "youtube_url",
            f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
        )
        nostrmedia_url = metadata.get("nostrmedia_url", "")

        if debug:
            print("\n=== DEBUG: Metadata ===")
            print(f"Title: {title}")
            print(f"Channel: {channel_title}")
            print(f"Published: {published_at}")
            print(
                f"Description length: {len(description) if description else 0} characters"
            )
            print(
                f"Using full_description: {'Yes' if 'full_description' in metadata else 'No'}"
            )

        # Create content for the Nostr event
        content = f"# {title}\n\n"

        # Add video embed - prioritize nostrmedia URL if available
        if nostrmedia_url:
            # Add nostrmedia URL for embedding
            content += f"{nostrmedia_url}\n\n"
            if debug:
                print(f"Embedding nostrmedia URL: {nostrmedia_url}")
        elif youtube_url:
            # Fallback to YouTube URL if nostrmedia not available
            content += f"{youtube_url}\n\n"
            if debug:
                print(f"Embedding YouTube URL: {youtube_url}")

        if channel_title:
            content += f"Channel: {channel_title}\n\n"
        if published_at:
            content += f"Published: {published_at}\n\n"

        # Add the full description
        if description:
            content += f"{description}\n\n"

        if debug:
            print("\n=== DEBUG: Event Content ===")
            print(content[:500] + "..." if len(content) > 500 else content)

        # Create a Nostr event (kind 1 = text note)
        kind = Kind(1)
        builder = EventBuilder(kind, content)

        # Add tags
        tags = []

        # Add subject tag with video title
        subject_tag = Tag.parse(["subject", title])
        tags.append(subject_tag)

        # Add hashtags
        tags.append(Tag.parse(["t", "video"]))
        if channel_title:
            # Convert channel title to a hashtag format (remove spaces, special chars)
            channel_hashtag = "".join(c for c in channel_title if c.isalnum())
            tags.append(Tag.parse(["t", channel_hashtag]))

        # Add video metadata as tags
        if video_id:
            # Add YouTube video ID tag
            tags.append(Tag.parse(["video_id", video_id]))

        # Add reference tags for URLs
        if nostrmedia_url:
            # Add nostrmedia URL as primary reference
            tags.append(Tag.parse(["r", nostrmedia_url]))

            # Add special media tag for better client support
            tags.append(Tag.parse(["media", nostrmedia_url]))

            # Add file type tag
            tags.append(Tag.parse(["m", "video/mp4"]))
        elif youtube_url:
            # Add YouTube URL as reference if nostrmedia not available
            tags.append(Tag.parse(["r", youtube_url]))

            # Add special YouTube embed tag that some clients recognize
            tags.append(Tag.parse(["youtube", video_id]))

            # Add media tag for better client support
            tags.append(Tag.parse(["m", "video/mp4"]))

        # We don't add a content warning tag as it's not needed for videos

        builder = builder.tags(tags)

        if debug:
            print("\n=== DEBUG: Event Tags ===")
            for tag in tags:
                print(f"Tag: {tag.as_vec()}")

        # Create a signer from keys
        signer = NostrSigner.keys(keys)

        if debug:
            print("\n=== DEBUG: Signer Created ===")
            print(f"Public key: {keys.public_key().to_hex()}")

        # Import asyncio here to avoid reference errors
        import asyncio

        # Set up the event loop for async operations
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If there's no event loop in the current thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Get relays from config or use defaults
        relays = get_nostr_relays()

        if debug:
            print("\n=== DEBUG: Relay Configuration ===")
            # Check if relays are from config or defaults
            config = load_config()
            using_config_relays = "nostr" in config and "relays" in config["nostr"]
            print(
                f"Using {len(relays)} relays from {'config' if using_config_relays else 'defaults'}"
            )

        if debug:
            print("\n=== DEBUG: Connecting to Relays ===")
            for relay in relays:
                print(f"Relay: {relay}")

        # Create client
        client = Client()

        # Set the signer
        try:
            client.signer = signer
            if debug:
                print("Signer set successfully")
        except Exception as e:
            print(f"Warning: Could not set signer on client: {e}")
            print("Events may not be signed correctly.")

        # Add relays
        for relay in relays:
            try:
                # Create relay options if needed
                # Note: We're not using options directly, but keeping this for future use

                # Try to add the relay
                if debug:
                    print(f"Adding relay: {relay}")

                # Check if add_relay is a coroutine
                if asyncio.iscoroutinefunction(client.add_relay):
                    loop.run_until_complete(client.add_relay(relay))
                else:
                    client.add_relay(relay)

                if debug:
                    print(f"Added relay: {relay}")
            except Exception as e:
                print(f"Error adding relay {relay}: {e}")

        # Connect to relays
        if asyncio.iscoroutinefunction(client.connect):
            loop.run_until_complete(client.connect())
        else:
            client.connect()

        if debug:
            print("\n=== DEBUG: Client Connected ===")

        # Sign and publish the event
        import asyncio

        # Set up the event loop for async operations
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If there's no event loop in the current thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Sign the event
        if debug:
            print("\n=== DEBUG: Signing Event ===")

        # Try different ways to sign the event
        try:
            # Method 1: Use the builder's sign method if available
            if hasattr(builder, "sign"):
                event = loop.run_until_complete(builder.sign(signer))
                if debug:
                    print("Event signed using builder.sign()")
            # Method 2: Use the to_event method if available
            elif hasattr(builder, "to_event"):
                event = builder.to_event(keys)
                if debug:
                    print("Event signed using builder.to_event()")
            # Method 3: Use the client to sign the event
            else:
                event = client.sign_event_builder(builder)
                if debug:
                    print("Event signed using client.sign_event_builder()")
        except Exception as e:
            print(f"Error signing event: {e}")
            raise

        if debug:
            print("Event signed successfully")
            print(f"Event ID: {event.id().to_hex()}")
            print(f"Event JSON: {event.as_json()}")

        # Publish the event
        if debug:
            print("\n=== DEBUG: Publishing Event ===")

        try:
            # Try different ways to publish the event
            if hasattr(client, "publish_event"):
                loop.run_until_complete(client.publish_event(event))
                if debug:
                    print("Event published using client.publish_event()")
            else:
                if asyncio.iscoroutinefunction(client.send_event):
                    loop.run_until_complete(client.send_event(event))
                else:
                    client.send_event(event)
                if debug:
                    print("Event published using client.send_event()")
        except Exception as e:
            print(f"Error publishing event: {e}")
            raise

        if debug:
            print("Event published successfully")

        # Wait for confirmation from relays
        time.sleep(1)

        # Disconnect from relays
        if asyncio.iscoroutinefunction(client.disconnect):
            loop.run_until_complete(client.disconnect())
        else:
            client.disconnect()

        # Create the result
        event_id = event.id().to_hex()
        pubkey = keys.public_key().to_hex()

        # Generate nostr: URI
        nostr_uri = f"nostr:note1{event_id}"

        # Generate web links to nostr viewers
        snort_link = f"https://snort.social/e/{event_id}"
        primal_link = f"https://primal.net/e/{event_id}"

        print("Video uploaded successfully to Nostr!")
        print(f"Event ID: {event_id}")
        print(f"View on Snort: {snort_link}")
        print(f"View on Primal: {primal_link}")

        return {
            "success": True,
            "event_id": event_id,
            "pubkey": pubkey,
            "nostr_uri": nostr_uri,
            "links": {"snort": snort_link, "primal": primal_link},
        }

    except Exception as e:
        print(f"Error uploading to Nostr: {str(e)}")
        return {"success": False, "error": str(e)}

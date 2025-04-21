# NosVid - YouTube Channel Downloader

A tool for downloading and managing YouTube videos, specifically designed for the Einundzwanzig Podcast channel.

## Features

- Retrieve video metadata from YouTube channels using the YouTube Data API
- Download videos using yt-dlp with configurable quality settings
- Track download history to avoid re-downloading videos
- Organize videos in a structured repository
- Support for incremental updates (only download new videos)
- Upload videos to nostrmedia.com
- Publish videos to the Nostr network
- Translate videos using HeyGen's AI video translation service
- Web interface for managing videos

## Setup

We recommend using a virtual environment for installing NosVid. For detailed setup instructions, see [Setup Guide](setup.md).

### Quick Installation

1. Clone the repository and create a virtual environment:

```bash
git clone https://github.com/yourusername/nosvid.git
cd nosvid
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install NosVid and its dependencies:

```bash
pip install -e .
```

3. Create a `config.yaml` file in the root directory with your configuration:

```yaml
# NosVid Configuration File

# YouTube API Configuration
youtube:
  api_key: "YOUR_YOUTUBE_API_KEY_HERE"
  # Path to cookies file for YouTube authentication (optional)
  # cookies_file: "~/youtube_cookies.txt"

# Nostr Configuration (optional, for nostrmedia and nostr functionality)
nostr:
  # Private key (hex or nsec format)
  nsec: "YOUR_NSEC_HERE"
  # Public key (hex or npub format)
  npub: "YOUR_NPUB_HERE"
  # Relays to use for publishing (optional, defaults will be used if not specified)
  # relays:
  #   - "wss://relay.damus.io"
  #   - "wss://nos.lol"
  #   - "wss://nostr.wine"
  #   - "wss://relay.nostr.band"
  #   - "wss://relay.snort.social"
  #   - "wss://relay.nostrudel.ninja"

# HeyGen API Configuration (optional, for video translation functionality)
heygen:
  api_key: "YOUR_HEYGEN_API_KEY_HERE"

# Default Settings
defaults:
  output_dir: "./repository"
  video_quality: "best"
  download_delay: 5
```

## Usage

NosVid provides a simple command-line interface with several main commands:

- `sync`: Sync metadata for all videos in a channel
- `list`: List videos in the repository
- `download`: Download videos
- `nostrmedia`: Upload videos to nostrmedia.com
- `nostr`: Publish videos to the Nostr network
- `heygen`: Translate videos using HeyGen
- `heygen-status`: Check the status of HeyGen translations
- `serve`: Start the web interface

### Quick Start

```bash
# Sync metadata for all videos
nosvid sync

# List all videos
nosvid list

# Download a specific video
nosvid download VIDEO_ID

# Download all pending videos
nosvid download

# Upload a video to nostrmedia.com
nosvid nostrmedia VIDEO_ID

# Publish a video to the Nostr network
nosvid nostr VIDEO_ID

# Check consistency of metadata.json files
nosvid consistency-check

# Fix inconsistencies in metadata.json files
nosvid consistency-check --fix

# Translate a video using HeyGen
nosvid heygen VIDEO_ID --language "Spanish"

# Check the status of a translation
nosvid heygen-status VIDEO_ID --language "Spanish"

# Start the web interface
nosvid serve
```

## Repository Structure

The downloaded videos are organized as follows:

```
repository/
└── Channel_Name/
    ├── metadata/
    │   ├── channel_info.json
    │   └── sync_history.json
    └── videos/
        ├── video_id1/
        │   ├── metadata.json (main metadata with references to all platforms)
        │   ├── youtube/
        │   │   ├── Title1.mp4
        │   │   ├── Title1.info.json
        │   │   ├── Title1.jpg
        │   │   ├── Title1.description
        │   │   └── metadata.json (YouTube-specific metadata)
        │   ├── nostrmedia/
        │   │   └── metadata.json (Nostrmedia-specific metadata)
        │   ├── nostr/
        │   │   └── metadata.json (Nostr-specific metadata)
        │   └── heygen/
        │       ├── free/
        │       │   ├── Spanish.mp4
        │       │   └── metadata.json (HeyGen free plan metadata)
        │       ├── pro/
        │       │   ├── German.mp4
        │       │   └── metadata.json (HeyGen pro plan metadata)
        │       └── scale/
        │           ├── French.mp4
        │           └── metadata.json (HeyGen scale plan metadata)
        └── video_id2/
            ├── metadata.json
            ├── youtube/
            │   └── ...
            ├── nostrmedia/
            │   └── ...
            └── nostr/
                └── ...
```

## Deployment

For information on deploying NosVid on a server, see the [Deployment Guide](deployment.md).

## Management

For information on managing NosVid, see the [Management Guide](management.md).

## License

This project is for personal use only. Please respect YouTube's terms of service and copyright laws.

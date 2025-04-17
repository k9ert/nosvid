# NosVid - YouTube Channel Downloader

A tool for downloading and managing YouTube videos, specifically designed for the Einundzwanzig Podcast channel.

## Features

- Retrieve video metadata from YouTube channels using the YouTube Data API
- Download videos using yt-dlp with configurable quality settings
- Track download history to avoid re-downloading videos
- Organize videos in a structured repository
- Support for incremental updates (only download new videos)

## Setup

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/nosvid.git
cd nosvid
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `config.yaml` file in the root directory with your configuration:

```yaml
# NosVid Configuration File

# YouTube API Configuration
youtube:
  api_key: "YOUR_YOUTUBE_API_KEY_HERE"

# Nostr Configuration (optional, for nostrmedia upload functionality)
nostr:
  # Private key (hex or nsec format)
  nsec: "YOUR_NSEC_HERE"
  # Public key (hex or npub format)
  npub: "YOUR_NPUB_HERE"

# Default Settings
defaults:
  output_dir: "./repository"
  video_quality: "best"
  download_delay: 5
```

Alternatively, you can still use a `youtube.key` file or `secrets.yaml` for backward compatibility.

### Optional Dependencies

For nostrmedia upload functionality, you'll need to install the nostr package:

```bash
pip install nostr
```

Note: The nostr package requires additional system dependencies. If you encounter issues installing it, you can still use the rest of the functionality without it.

### Development Installation

For development, you can install the package in development mode:

```bash
pip install -e .
```

## Usage

NosVid provides a simple command-line interface with four main commands:

- `sync`: Sync metadata for all videos in a channel
- `list`: List videos in the repository
- `download`: Download videos
- `nostrmedia`: Upload videos to nostrmedia.com

### Quick Start

```bash
# Sync metadata for all videos
./nosvid sync

# List all videos
./nosvid list

# Download a specific video
./nosvid download VIDEO_ID

# Download all pending videos
./nosvid download

# Upload a video to nostrmedia.com
./nosvid nostrmedia VIDEO_ID
```

### Sync Metadata

To sync metadata for all videos without downloading the actual video files:

```bash
./nosvid sync
```

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--max-videos`: Maximum number of videos to sync (None for all)
- `--delay`: Delay between operations in seconds (default: 5)

### List Videos

To list all videos in the repository:

```bash
./nosvid list
```

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--downloaded`: Show only downloaded videos
- `--not-downloaded`: Show only videos that have not been downloaded

### Download Videos

To download a specific video by ID:

```bash
./nosvid download VIDEO_ID
```

To download all videos that have not been downloaded yet:

```bash
./nosvid download
```

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--quality`: Video quality (default: best)
- `--delay`: Delay between downloads in seconds (default: 5)

### Upload to Nostrmedia

To upload a video to nostrmedia.com:

```bash
./nosvid nostrmedia VIDEO_ID
```

You can also provide a private key for signing the upload:

```bash
./nosvid nostrmedia VIDEO_ID --private-key YOUR_PRIVATE_KEY
```

The private key can be in hex format or nsec format (bech32-encoded). If not provided, it will try to use the one from your `config.yaml` file. If no key is found in the config, a new one will be generated.

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--private-key`: Private key string (hex or nsec format, if not provided, will use from config or generate a new one)

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
        │   └── nostrmedia/
        │       └── metadata.json (Nostrmedia-specific metadata)
        └── video_id2/
            ├── metadata.json
            ├── youtube/
            │   └── ...
            └── nostrmedia/
                └── ...
```

### Migration

If you have an existing repository with the old structure, you can migrate it to the new structure using the provided migration script:

```bash
python migrate_repository.py /path/to/Channel_Name
```

## Syncing to a Repository

To maintain a repository of videos:

1. Set up a regular schedule to run the sync command
2. Use version control (like Git) to track changes to the metadata
3. Consider using Git LFS for the video files if using GitHub or similar platforms

## Caution

- Be mindful of YouTube's terms of service
- Respect copyright and fair use policies
- Be careful with bandwidth usage and storage requirements
- Consider rate limiting to avoid API quota issues

## License

This project is for personal use only. Please respect YouTube's terms of service and copyright laws.

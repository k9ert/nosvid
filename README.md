# NosVid - YouTube Channel Downloader

A tool for downloading and managing YouTube videos, specifically designed for the Einundzwanzig Podcast channel.

## Features

- Retrieve video metadata from YouTube channels using the YouTube Data API
- Download videos using yt-dlp with configurable quality settings
- Track download history to avoid re-downloading videos
- Organize videos in a structured repository
- Support for incremental updates (only download new videos)

## Setup

We recommend using a virtual environment for installing NosVid. For detailed setup instructions, see [SETUP.md](SETUP.md).

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

### Optional Features

For nostrmedia and nostr functionality, install with the nostr extra:

```bash
pip install -e .[nostr]
```

For development (includes testing tools), install with the dev extra:

```bash
pip install -e .[dev]
```

Note: The nostr-sdk package is used for nostrmedia and nostr functionality. If you encounter issues installing it, you can still use the rest of the functionality without it.

## Usage

NosVid provides a simple command-line interface with several main commands:

- `sync`: Sync metadata for all videos in a channel
- `list`: List videos in the repository
- `download`: Download videos
- `nostrmedia`: Upload videos to nostrmedia.com
- `nostr`: Publish videos to the Nostr network
- `heygen`: Translate videos using HeyGen
- `heygen-status`: Check the status of HeyGen translations

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
```

### Consistency Check

To check the consistency of metadata.json files for all videos:

```bash
nosvid consistency-check
```

To automatically fix inconsistencies:

```bash
nosvid consistency-check --fix
```

This command checks all videos in the repository, recreates the metadata.json files, and reports any differences. It's useful for ensuring that all metadata is up-to-date and consistent, including npub extraction from chat and description files.

### Sync Metadata

To sync metadata for all videos without downloading the actual video files:

```bash
nosvid sync
```

To sync metadata for a specific video:

```bash
nosvid sync VIDEO_ID
```

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--max-videos`: Maximum number of videos to sync (default: 5, use 0 for all)
- `--delay`: Delay between operations in seconds (default: 5)
- `--force-refresh`: Force refresh from YouTube API even if cache is fresh

#### YouTube API Caching

To minimize YouTube API quota usage, the tool caches the channel video list for 24 hours. When you run the sync command, it will:

1. Check if a cached video list exists for the channel
2. If the cache exists and is less than 24 hours old, use it instead of calling the YouTube API
3. If the cache is older than 24 hours or doesn't exist, fetch the video list from the YouTube API
4. If you want to force a refresh from the API regardless of cache age, use the `--force-refresh` flag

#### Efficient Video Processing

The sync command processes videos efficiently:

1. It filters out videos that are already synced
2. It processes videos in chronological order (oldest first)
3. It only processes new videos up to the specified `--max-videos` limit
4. Each time you run the command with a limit, it will process the next batch of new videos
5. This ensures you can gradually sync all videos without hitting API quotas

### List Videos

To list all videos in the repository:

```bash
nosvid list
```

The list command shows a comprehensive repository status summary at the beginning, including:

1. The total number of videos in the cache
2. The number of videos with metadata (and percentage)
3. The number of downloaded videos (and percentage)
4. The number of videos uploaded to Nostrmedia (and percentage)
5. The number of videos posted to Nostr (and percentage)
6. The number of videos with npubs (and percentage)
7. The total number of npubs found

The videos are listed in chronological order (oldest first) with their status in the format:

```
[YT:✓|NM:✓|NS:✓] VIDEO_ID (DATE) [ENGAGEMENT] DURATION - TITLE
```

Where:
- `YT`: YouTube download status (✓ if downloaded)
- `NM`: Nostrmedia upload status (✓ if uploaded)
- `NS`: Nostr post status (✓ if posted once, a number if posted multiple times)

The engagement column shows an orange bar representing the number of npubs found in the video's chat and description files. The bar is capped at 10 npubs for display purposes.

For example:

```
Repository Status:
------------------------------------------------------------
Videos in cache (YT):     434
Metadata (YT):              47 / 434 (10.8%)
Downloaded (YT):             4 / 434 (0.9%)
Uploaded (NM):               3 / 434 (0.7%)
Videos with npubs:           6 / 434 (1.4%)
Total npubs found:        9
------------------------------------------------------------

Found 17 videos:
----------------------------------------------------------------------------------------------------
  1. [YT: |NM: ] RvZJnzslz3k (2025-04-17) [          ] 65.1 min - 🔴 Einundzwanzig Live #17 - ACHTUNG: MASSIVE PREMIUMTURBO BITCOIN CANDLE
  2. [YT:✓|NM: ] Eqn5l8S3WXw (2025-04-16) [          ] 9.9 min - Bitcoin Seedphrase | Das musst du wissen
  3. [YT: |NM: ] YjFgaDOrGmo (2025-03-27) [██        ] 73.0 min - 🔴 Einundzwanzig Live #14 - Mit Tanja, Daniel und Finn
```

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--downloaded`: Show only downloaded videos
- `--not-downloaded`: Show only videos that have not been downloaded

### Download Videos

To download a specific video by ID:

```bash
nosvid download VIDEO_ID
```

To download the oldest video that hasn't been downloaded yet (default behavior):

```bash
nosvid download
```

To download all videos that have not been downloaded yet:

```bash
nosvid download --all-pending
```

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--all-pending`: Download all videos that haven't been downloaded yet
- `--quality`: Video quality (default: best)
- `--delay`: Delay between downloads in seconds (default: 5)

### Upload to Nostrmedia

To upload a video to nostrmedia.com:

```bash
nosvid nostrmedia VIDEO_ID
```

You can also provide a private key for signing the upload:

```bash
./nosvid nostrmedia VIDEO_ID --private-key YOUR_PRIVATE_KEY
```

The private key can be in hex format or nsec format (bech32-encoded). If not provided, it will try to use the one from your `config.yaml` file. If no key is found in the config, a new one will be generated.

#### Automatic Backtracking

The `nostrmedia` command includes automatic backtracking functionality:

1. If the video hasn't been downloaded yet, it will automatically download it first
2. If the video metadata hasn't been synced yet, it will automatically sync it first

This means you can simply run:

```bash
nosvid nostrmedia VIDEO_ID
```

And the tool will handle all the necessary steps to upload the video to nostrmedia.com, even if you haven't synced or downloaded the video yet.

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--private-key`: Private key string (hex or nsec format, if not provided, will use from config or generate a new one)
- `--debug`: Enable debug output for detailed information about the upload process

### Publish to Nostr

To publish a specific video to the Nostr network:

```bash
nosvid nostr VIDEO_ID
```

To publish the oldest video that hasn't been posted to Nostr yet (default behavior):

```bash
nosvid nostr
```

This command creates a Nostr note with the video metadata and embeds the video. If the video has already been uploaded to nostrmedia.com, it will use the nostrmedia URL for embedding. Otherwise, it will use the YouTube URL.

You can post the same video multiple times to Nostr. Each post is stored in a time-sorted array in the metadata, allowing you to track all posts for a video.

#### Automatic Backtracking

The `nostr` command includes automatic backtracking functionality:

1. If the video hasn't been uploaded to nostrmedia yet, it will automatically upload it first
2. If the video hasn't been downloaded yet, it will automatically download it first
3. If the video metadata hasn't been synced yet, it will automatically sync it first

This means you can simply run:

```bash
nosvid nostr VIDEO_ID
```

And the tool will handle all the necessary steps to publish the video to Nostr, even if you haven't synced, downloaded, or uploaded the video yet.

You can also provide a private key for signing the note:

```bash
./nosvid nostr VIDEO_ID --private-key YOUR_PRIVATE_KEY
```

The private key can be in hex format or nsec format (bech32-encoded). If not provided, it will try to use the one from your `config.yaml` file.

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--private-key`: Private key string (hex or nsec format, if not provided, will use from config)
- `--debug`: Enable debug output for detailed information about the publishing process

### Translate Videos with HeyGen

To translate a video using HeyGen's AI video translation service:

```bash
nosvid heygen VIDEO_ID --language "Spanish"
```

To list all supported languages:

```bash
nosvid heygen --list-languages
```

To translate a video and wait for the translation to complete:

```bash
nosvid heygen VIDEO_ID --language "Spanish" --wait --download
```

The HeyGen integration supports different quality levels that correspond to HeyGen's subscription plans:

- `free`: Uses the free plan (includes watermark)
- `pro`: Uses the Pro plan features
- `scale`: Uses the Scale plan features (includes video translation API)

Each quality level is stored in a separate directory to prevent overwriting translations from different quality levels.

#### Automatic Backtracking

The `heygen` command includes automatic backtracking functionality:

1. If the video hasn't been downloaded yet, it will use the YouTube URL from metadata
2. If the video metadata hasn't been synced yet, it will prompt you to sync it first

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--language`: Target language for translation (default: English)
- `--quality`: Quality level of the translation (free, pro, scale) (default: free)
- `--url`: URL of the video to translate (if not provided, will use YouTube URL from metadata)
- `--wait`: Wait for translation to complete
- `--timeout`: Maximum time to wait for translation in seconds (default: 3600)
- `--check-interval`: Time between status checks in seconds (default: 30)
- `--download`: Download the translated video when complete
- `--force`: Force retranslation even if already translated
- `--list-languages`: List supported languages and exit
- `--debug`: Enable debug output

### Check HeyGen Translation Status

To check the status of a HeyGen translation:

```bash
nosvid heygen-status VIDEO_ID --language "Spanish"
```

To check the status and download the translated video if it's complete:

```bash
nosvid heygen-status VIDEO_ID --language "Spanish" --download
```

Options:
- `--output-dir`: Base directory for downloads (default: ./repository)
- `--language`: Language of the translation to check (default: English)
- `--quality`: Quality level of the translation (free, pro, scale) (default: free)
- `--download`: Download the translated video if complete
- `--debug`: Enable debug output

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

### Migration

If you have an existing repository with the old structure, you can migrate it to the new structure using the provided migration script:

```bash
python migrate_repository.py /path/to/Channel_Name
```

#### Duration Migration

If you have videos that were synced before the duration feature was added, you can use the provided migration script to extract the duration from the info.json files and add it to the metadata.json files:

```bash
python migrate_duration.py --repository-dir ./repository
```

This script will:
1. Find all video directories in the repository
2. Extract the duration from the info.json files
3. Update both the main metadata.json and the YouTube-specific metadata.json with the duration information

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

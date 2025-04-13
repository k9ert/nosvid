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

3. Make sure you have a YouTube API key in `youtube.key` file or in `secrets.yaml`

### Development Installation

For development, you can install the package in development mode:

```bash
pip install -e .
```

## Usage

NosVid provides a simple command-line interface with three main commands:

- `sync`: Sync metadata for all videos in a channel
- `list`: List videos in the repository
- `download`: Download videos

### Quick Start

```bash
# Sync metadata for all videos
./nosvid sync --output-dir ./downloads

# List all videos
./nosvid list --output-dir ./downloads

# Download a specific video
./nosvid download VIDEO_ID --output-dir ./downloads

# Download all pending videos
./nosvid download --output-dir ./downloads
```

### Sync Metadata

To sync metadata for all videos without downloading the actual video files:

```bash
./nosvid sync --output-dir ./downloads
```

Options:
- `--output-dir`: Base directory for downloads (default: ~/Downloads/nosvid)
- `--max-videos`: Maximum number of videos to sync (None for all)
- `--delay`: Delay between operations in seconds (default: 5)

### List Videos

To list all videos in the repository:

```bash
./nosvid list --output-dir ./downloads
```

Options:
- `--output-dir`: Base directory for downloads (default: ~/Downloads/nosvid)
- `--downloaded`: Show only downloaded videos
- `--not-downloaded`: Show only videos that have not been downloaded

### Download Videos

To download a specific video by ID:

```bash
./nosvid download VIDEO_ID --output-dir ./downloads
```

To download all videos that have not been downloaded yet:

```bash
./nosvid download --output-dir ./downloads
```

Options:
- `--output-dir`: Base directory for downloads (default: ~/Downloads/nosvid)
- `--quality`: Video quality (default: best)
- `--delay`: Delay between downloads in seconds (default: 5)

## Repository Structure

The downloaded videos are organized as follows:

```
downloads/
└── Channel_Name/
    ├── metadata/
    │   ├── channel_info.json
    │   └── download_history.json
    └── videos/
        ├── video_id1/
        │   ├── Title1.mp4
        │   ├── Title1.info.json
        │   ├── Title1.jpg
        │   ├── Title1.description
        │   └── metadata.json
        └── video_id2/
            ├── Title2.mp4
            ├── Title2.info.json
            └── ...
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

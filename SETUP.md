# NosVid Setup Guide

This guide will walk you through setting up NosVid using a virtual environment.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- virtualenv (recommended for creating isolated Python environments)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/nosvid.git
cd nosvid
```

### 2. Create and Activate a Virtual Environment

#### On Linux/macOS:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

#### On Windows:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

### 3. Install NosVid and its Dependencies

```bash
# Install the package and its dependencies
pip install -e .
```

For nostrmedia upload functionality, install with the nostrmedia extra:

```bash
pip install -e .[nostrmedia]
```

For development, install with the dev extra:

```bash
pip install -e .[dev]
```

### 4. Create a Configuration File

Create a `config.yaml` file in the root directory with your configuration:

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

### 5. Verify Installation

```bash
# Check if nosvid is installed correctly
nosvid --help
```

## Usage

After installation, you can use NosVid directly from the command line:

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
```

## Deactivating the Virtual Environment

When you're done using NosVid, you can deactivate the virtual environment:

```bash
deactivate
```

## Troubleshooting

### Missing Dependencies

If you encounter errors about missing dependencies, try reinstalling with all extras:

```bash
pip install -e .[nostrmedia,dev]
```

### Permission Issues

If you encounter permission issues when installing packages, try using the `--user` flag:

```bash
pip install --user -e .
```

### Nostr Package Installation Issues

The nostr package requires additional system dependencies. If you encounter issues installing it, you can still use the rest of the functionality without it.

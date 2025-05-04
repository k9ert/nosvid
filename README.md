# NosVid & DecData: Video Collection and Decentralized Distribution

[![CI](https://github.com/k9ert/nosvid/actions/workflows/ci.yml/badge.svg)](https://github.com/k9ert/nosvid/actions/workflows/ci.yml)
[![Python Tests](https://github.com/k9ert/nosvid/actions/workflows/pytest.yml/badge.svg)](https://github.com/k9ert/nosvid/actions/workflows/pytest.yml)
[![codecov](https://codecov.io/gh/k9ert/nosvid/branch/main/graph/badge.svg)](https://codecov.io/gh/k9ert/nosvid)

This repository contains two integrated projects:

1. **NosVid**: A tool for downloading and managing YouTube videos, specifically designed for the Einundzwanzig Podcast channel.
2. **DecData**: A peer-to-peer network application for distributing video content collected by NosVid.

## NosVid

NosVid is a comprehensive YouTube video management tool that allows you to:

- Retrieve video metadata from YouTube channels using the YouTube Data API
- Download videos using yt-dlp with configurable quality settings
- Track download history to avoid re-downloading videos
- Organize videos in a structured repository
- Upload videos to nostrmedia.com
- Publish videos to the Nostr network
- Translate videos using HeyGen's AI video translation service

[Learn more about NosVid](docs/nosvid.md)

## DecData

DecData is a peer-to-peer network application that enables:

- Decentralized distribution of video content
- Peer-to-peer file sharing without relying on centralized servers
- Video catalog synchronization across the network
- Efficient file transfer between peers
- Content verification with hash checking
- Search functionality across the distributed network

[Learn more about DecData](docs/decdata.md)

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/k9ert/nosvid.git
cd nosvid

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package and its dependencies
pip install -e .
```

### Development Setup

For development, you can use the provided setup script:

```bash
# Run the setup script
./scripts/setup_dev_environment.sh
```

This script will:
- Create a virtual environment if it doesn't exist
- Install development dependencies
- Set up pre-commit hooks

Alternatively, you can set up the development environment manually:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

The pre-commit hooks will automatically format your code using Black and sort imports with isort when you commit changes. Additional hooks for flake8 and mypy are available in the configuration but are commented out until the codebase is cleaned up.

### Basic Usage

#### NosVid

```bash
# Sync metadata for videos
nosvid sync

# List videos in the repository
nosvid list

# Download a video
nosvid download VIDEO_ID

# Start the web interface
nosvid serve
```

#### DecData

```bash
# Start a DecData node
decdata start

# Connect to another node
decdata connect --host 192.168.1.100 --port 2122

# Search for videos
decdata search "bitcoin podcast"

# Download a video
decdata download VIDEO_ID
```

## Testing

```bash
# Run all tests
./nosvid test

# Run only unit tests
./nosvid test --unit

# Run only integration tests
./nosvid test --integration

# Run tests with coverage
./nosvid test --coverage
```

For more information about testing, see the [Testing Documentation](tests/README.md).

## Documentation

- [NosVid Documentation](docs/nosvid.md)
- [DecData Documentation](docs/decdata.md)
- [Setup Guide](docs/setup.md)
- [Deployment Guide](docs/deployment.md)
- [Management Guide](docs/management.md)
- [Testing Documentation](tests/README.md)

## License

This project is for personal use only. Please respect YouTube's terms of service and copyright laws.

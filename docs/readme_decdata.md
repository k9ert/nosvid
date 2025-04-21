# DecData: Decentralized Video Data Exchange

DecData is a peer-to-peer network application for distributing video content collected by the NosVid project. While NosVid focuses on sourcing videos from YouTube and processing them for services like nostrmedia, DecData enables the decentralized exchange of this data between peers without relying on centralized servers.

## Project Overview

This project aims to create a resilient, decentralized infrastructure for preserving and sharing important video content. By leveraging peer-to-peer technology, DecData ensures that video content remains available even if the original sources become unavailable.

## Features

- **Peer-to-Peer Architecture**: Built on the p2pnetwork framework for robust decentralized communication
- **Video Catalog Synchronization**: Share and discover video metadata across the network
- **Efficient File Transfer**: Transfer video files directly between peers
- **Content Verification**: Ensure data integrity with hash verification
- **Search Functionality**: Find videos across the distributed network
- **Resumable Downloads**: Continue interrupted downloads from different peers
- **Integration with NosVid**: Seamless sharing of videos collected by NosVid

## Architecture

DecData uses a fully decentralized peer-to-peer architecture:

```
DecData P2P Network
│
├── Node Discovery & Connection
│   ├── Automatic peer discovery
│   └── Connection management
│
├── Distributed Video Catalog
│   ├── Metadata synchronization
│   └── Content availability tracking
│
├── Data Exchange Protocol
│   ├── Search functionality
│   ├── File transfer protocol
│   └── Integrity verification
│
└── NosVid Integration
    ├── Repository monitoring
    └── Automatic sharing
```

## Getting Started

### Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- p2pnetwork package (already installed in your environment)
- NosVid (optional, for video collection)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/decdata.git
cd decdata
```

2. Install dependencies (if not already installed):
```bash
pip install p2pnetwork
```

## Usage

### Starting a Node

```bash
# Start a DecData node on the default port (2122)
python run_node.py

# Start a node on a specific port
python run_node.py --port 2123

# Start a node with a specific directory to share
python run_node.py --port 2123 --share-dir /path/to/videos

# Start a node with NosVid integration
python run_node.py --nosvid-repo /path/to/nosvid/repository

# Start a node with custom NosVid API URL
python run_node.py --nosvid-api-url http://localhost:2121/api
```

### Connecting to Other Nodes

```bash
# Connect to another node
python connect_to_node.py --host 192.168.1.100 --port 2122

# Connect with a shared directory
python connect_to_node.py --host 192.168.1.100 --port 2122 --share-dir /path/to/videos

# Connect with NosVid integration
python connect_to_node.py --host 192.168.1.100 --port 2122 --nosvid-repo /path/to/nosvid/repository
```

### Searching for Videos

```bash
# Search for videos by title
python -m decdata.node search "bitcoin podcast"

# Search for videos by ID
python -m decdata.node search --id VIDEO_ID
```

### Downloading Videos

```bash
# Download a video by ID
python -m decdata.node download VIDEO_ID

# Download a video to a specific location
python -m decdata.node download VIDEO_ID --output /path/to/save
```

## Integration with NosVid

DecData is designed to work seamlessly with the NosVid project:

1. NosVid collects videos from YouTube and processes them
2. DecData monitors the NosVid repository for new videos
3. DecData shares these videos with other peers in the network
4. Other peers can discover and download these videos

To enable NosVid integration:

```bash
python -m decdata.node start --nosvid-repo /path/to/nosvid/repository
```

## Development Roadmap

- **Phase 1**: Basic peer-to-peer networking and file sharing
- **Phase 2**: Distributed video catalog and search functionality
- **Phase 3**: NosVid integration and automatic sharing
- **Phase 4**: Enhanced security and privacy features
- **Phase 5**: Web and mobile interfaces

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

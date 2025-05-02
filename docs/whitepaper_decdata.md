# DecData Protocol Whitepaper

## Introduction

DecData is a peer-to-peer protocol designed for decentralized video data exchange. It enables nodes to discover, search, and share video content across a distributed network, with a focus on preserving content from platforms like YouTube. This document outlines the core concepts, message types, and behaviors of the DecData protocol.

## Network Architecture

DecData employs a fully decentralized peer-to-peer architecture where each node:
- Maintains its own catalog of videos
- Connects directly to other nodes without central coordination
- Synchronizes with a local NosVid API instance for content management
- Participates in network-wide content discovery and distribution

## Node Communication

Nodes communicate through JSON-formatted messages. Each message contains a `type` field that determines how it will be processed. Messages are exchanged directly between connected nodes.

## Message Types

### 1. Catalog Exchange

**Message: `catalog`**
- Sent automatically when nodes connect
- Contains the list of video IDs available on the sending node
- Enables nodes to build a map of content availability across the network

```json
{
  "type": "catalog",
  "node_id": "sender_node_id",
  "videos": ["video_id_1", "video_id_2", ...]
}
```

### 2. Content Search

**Message: `search`**
- Initiates a search across the network
- Can search by video ID or text query
- Propagates to all connected nodes

```json
{
  "type": "search",
  "search_id": "unique_search_identifier",
  "query": "optional_text_query",
  "video_id": "optional_specific_video_id"
}
```

**Message: `search_result`**
- Response to a search request
- Contains matching videos from the responding node

```json
{
  "type": "search_result",
  "search_id": "original_search_identifier",
  "node_id": "responder_node_id",
  "results": [video_metadata_objects]
}
```

### 3. Content Retrieval

**Message: `download_request`**
- Requests a specific video from a node
- Identified by a unique request ID

```json
{
  "type": "download_request",
  "request_id": "unique_request_identifier",
  "video_id": "requested_video_id"
}
```

**Message: `file_data`**
- Contains the requested video data
- Includes hash for integrity verification

```json
{
  "type": "file_data",
  "request_id": "original_request_identifier",
  "video_id": "video_id",
  "file_hash": "sha256_hash_of_file",
  "file_size": size_in_bytes,
  "file_data": "hex_encoded_binary_data"
}
```

**Message: `download_error`**
- Indicates an error during download
- Provides error details

```json
{
  "type": "download_error",
  "request_id": "original_request_identifier",
  "error": "error_description"
}
```

### 4. Metadata Exchange

**Message: `video_info_request`**
- Requests metadata for a specific video

```json
{
  "type": "video_info_request",
  "request_id": "unique_request_identifier",
  "video_id": "requested_video_id"
}
```

**Message: `video_info_response`**
- Contains metadata for the requested video

```json
{
  "type": "video_info_response",
  "request_id": "original_request_identifier",
  "success": true/false,
  "video_info": video_metadata_object,
  "error": "error_description_if_not_successful"
}
```

### 5. Simple Messaging

**Message: `message`**
- Used for direct text communication between nodes
- Primarily for interactive mode and debugging

```json
{
  "type": "message",
  "content": "text_message"
}
```

## Node Behavior

### Connection Establishment
When nodes connect:
1. They exchange node IDs
2. They automatically share their video catalogs
3. They maintain a map of which videos are available on which peers

### Content Discovery
To find content:
1. A node sends a `search` message to all connected peers
2. Peers respond with `search_result` messages containing matching content
3. The originating node aggregates results from all responding peers

### Content Retrieval
To download content:
1. A node identifies which peer has the desired video
2. It sends a `download_request` to that peer
3. The peer responds with `file_data` containing the video
4. The receiving node verifies the file hash for integrity
5. If verification succeeds, the node adds the video to its local catalog

### Metadata Retrieval
To get video information:
1. A node sends a `video_info_request` to a peer with the video
2. The peer responds with a `video_info_response` containing metadata
3. This allows nodes to preview content before downloading

## Integration with NosVid

DecData nodes integrate with a local NosVid API instance to:
1. Source their initial video catalog
2. Store downloaded videos in a structured repository
3. Provide a consistent metadata format across the network
4. Enable additional features like Nostr publishing and nostrmedia integration

## Conclusion

The DecData protocol provides a simple yet effective mechanism for decentralized video sharing. By combining peer-to-peer networking with local API integration, it creates a resilient system for preserving and distributing video content across a distributed network of nodes.

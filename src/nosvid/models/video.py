"""
Video model for nosvid
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Platform:
    """
    Platform information for a video

    Attributes:
        name: Platform name (e.g., 'youtube', 'nostrmedia')
        url: URL of the video on the platform
        downloaded: Whether the video has been downloaded
        downloaded_at: When the video was downloaded
        uploaded: Whether the video has been uploaded
        uploaded_at: When the video was uploaded
    """

    name: str
    url: str
    downloaded: bool = False
    downloaded_at: Optional[str] = None
    uploaded: bool = False
    uploaded_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Platform":
        """
        Create a Platform from a dictionary

        Args:
            data: Dictionary representation of a Platform

        Returns:
            Platform object
        """
        return cls(
            name=data.get("name", ""),
            url=data.get("url", ""),
            downloaded=data.get("downloaded", False),
            downloaded_at=data.get("downloaded_at"),
            uploaded=data.get("uploaded", False),
            uploaded_at=data.get("uploaded_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization

        Returns:
            Dictionary representation of the Platform
        """
        return {
            "name": self.name,
            "url": self.url,
            "downloaded": self.downloaded,
            "downloaded_at": self.downloaded_at,
            "uploaded": self.uploaded,
            "uploaded_at": self.uploaded_at,
        }


@dataclass
class NostrPost:
    """
    Nostr post information

    Attributes:
        event_id: Nostr event ID
        pubkey: Public key that created the post
        uploaded_at: When the post was created
        nostr_uri: URI for the post
        links: Links to the post on various platforms
    """

    event_id: str
    pubkey: str
    uploaded_at: str
    nostr_uri: Optional[str] = None
    links: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NostrPost":
        """
        Create a NostrPost from a dictionary

        Args:
            data: Dictionary representation of a NostrPost

        Returns:
            NostrPost object
        """
        return cls(
            event_id=data.get("event_id", ""),
            pubkey=data.get("pubkey", ""),
            uploaded_at=data.get("uploaded_at", datetime.now().isoformat()),
            nostr_uri=data.get("nostr_uri"),
            links=data.get("links", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization

        Returns:
            Dictionary representation of the NostrPost
        """
        return {
            "event_id": self.event_id,
            "pubkey": self.pubkey,
            "uploaded_at": self.uploaded_at,
            "nostr_uri": self.nostr_uri,
            "links": self.links,
        }


@dataclass
class Video:
    """
    Video information

    Attributes:
        video_id: Unique identifier for the video
        title: Title of the video
        published_at: When the video was published
        duration: Duration of the video in seconds
        platforms: Information about the video on different platforms
        nostr_posts: Nostr posts for the video
        npubs: Nostr public keys mentioned in the video
        synced_at: When the video metadata was last synced
    """

    video_id: str
    title: str
    published_at: str
    duration: int = 0
    platforms: Dict[str, Platform] = field(default_factory=dict)
    nostr_posts: List[NostrPost] = field(default_factory=list)
    npubs: Dict[str, List[str]] = field(default_factory=dict)
    synced_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Video":
        """
        Create a Video from a dictionary

        Args:
            data: Dictionary representation of a Video

        Returns:
            Video object
        """
        platforms = {}
        if "platforms" in data:
            for name, platform_data in data["platforms"].items():
                platform_data["name"] = name
                platforms[name] = Platform.from_dict(platform_data)

        nostr_posts = []
        if (
            "platforms" in data
            and "nostr" in data["platforms"]
            and "posts" in data["platforms"]["nostr"]
        ):
            for post_data in data["platforms"]["nostr"]["posts"]:
                nostr_posts.append(NostrPost.from_dict(post_data))

        return cls(
            video_id=data.get("video_id", ""),
            title=data.get("title", ""),
            published_at=data.get("published_at", ""),
            duration=data.get("duration", 0),
            platforms=platforms,
            nostr_posts=nostr_posts,
            npubs=data.get("npubs", {}),
            synced_at=data.get("synced_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization

        Returns:
            Dictionary representation of the Video
        """
        platforms_dict = {}
        for name, platform in self.platforms.items():
            platforms_dict[name] = platform.to_dict()

        # Special handling for nostr posts
        if "nostr" in platforms_dict and self.nostr_posts:
            if "posts" not in platforms_dict["nostr"]:
                platforms_dict["nostr"]["posts"] = []
            platforms_dict["nostr"]["posts"] = [
                post.to_dict() for post in self.nostr_posts
            ]

        return {
            "video_id": self.video_id,
            "title": self.title,
            "published_at": self.published_at,
            "duration": self.duration,
            "platforms": platforms_dict,
            "npubs": self.npubs,
            "synced_at": self.synced_at,
        }

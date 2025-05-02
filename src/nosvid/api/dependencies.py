"""
Dependency injection for nosvid API
"""

from fastapi import Depends

from ..services.config_service import ConfigService
from ..services.video_service import VideoService
from ..repo.video_repo import FileSystemVideoRepo


def get_config_service():
    """Get the configuration service"""
    return ConfigService()


def get_video_repository(config_service: ConfigService = Depends(get_config_service)):
    """Get the video repository"""
    output_dir = config_service.get_output_dir()
    return FileSystemVideoRepo(output_dir)


def get_video_service(video_repository: FileSystemVideoRepo = Depends(get_video_repository)):
    """Get the video service"""
    return VideoService(video_repository)


def get_channel_title(config_service: ConfigService = Depends(get_config_service)):
    """Get the channel title"""
    return config_service.get_channel_title()

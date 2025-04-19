"""
Scheduler service for nosvid with hardcoded scheduled tasks
"""

import os
import logging
import os.path
from typing import Dict, Any, List, Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

# Import the functions we want to call directly
from ..metadata.sync import sync_metadata
from ..download.video import download_video
from ..nostr.upload import post_to_nostr
from ..nostrmedia.upload import upload_to_nostrmedia
from ..utils.config import get_channel_id, get_default_video_quality, load_config, get_youtube_api_key, get_repository_dir
# We're using list_videos instead of these helper functions
# from ..utils.find_oldest import find_oldest_video_without_download, find_oldest_video_without_nostr_post, find_oldest_video_without_nostrmedia

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    """
    Service for managing hardcoded scheduled jobs
    """
    _instance = None

    def __new__(cls):
        """
        Singleton pattern to ensure only one scheduler instance
        """
        if cls._instance is None:
            cls._instance = super(SchedulerService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Initialize the scheduler service
        """
        if self._initialized:
            return

        self._initialized = True
        self.scheduler = BackgroundScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone='UTC'
        )
        self.jobs = {}

        # Start the scheduler
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler service initialized")

            # Set up hardcoded jobs
            self._setup_hardcoded_jobs()

    def _setup_hardcoded_jobs(self):
        """
        Set up hardcoded scheduled jobs
        """
        # 1. Hourly sync job with force refresh - runs every hour at minute 0
        self._add_hourly_sync_job()

        # 2. Regular sync job - runs every 5 minutes
        self._add_regular_sync_job()

        # 3. Daily download job - runs every day at 2 AM
        self._add_daily_download_job()

        # 4. Regular download job - runs every 5 minutes, downloads 5 videos
        self._add_regular_download_job()

        # 5. Weekly nostr posting job - runs every Sunday at 3 AM
        self._add_weekly_nostr_job()

        # 6. Regular nostrmedia upload job - runs every 5 minutes
        self._add_regular_nostrmedia_job()

        # Log all scheduled jobs
        self._log_job_schedule()

    def _add_hourly_sync_job(self):
        """
        Add hourly sync job to the scheduler
        """
        job_id = 'hourly_sync'
        cron_expression = '0 * * * *'  # Every hour at minute 0
        description = 'Sync metadata for new videos every hour'

        try:
            # Add the job to the scheduler
            job = self.scheduler.add_job(
                self._run_sync_job,
                trigger=CronTrigger.from_crontab(cron_expression),
                id=job_id,
                replace_existing=True
            )

            # Store job metadata
            self.jobs[job_id] = {
                'id': job_id,
                'command': 'sync',
                'args': ['--force-refresh', '--max-videos', '5'],
                'schedule': cron_expression,
                'enabled': True,
                'description': description,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

            logger.info(f"Added job {job_id} with schedule {cron_expression}")
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {str(e)}")

    def _add_daily_download_job(self):
        """
        Add daily download job to the scheduler
        """
        job_id = 'daily_download'
        cron_expression = '0 2 * * *'  # Every day at 2 AM
        description = 'Download the oldest pending video every day'

        try:
            # Add the job to the scheduler
            job = self.scheduler.add_job(
                self._run_download_job,
                trigger=CronTrigger.from_crontab(cron_expression),
                id=job_id,
                replace_existing=True
            )

            # Store job metadata
            self.jobs[job_id] = {
                'id': job_id,
                'command': 'download',
                'args': ['--oldest'],
                'schedule': cron_expression,
                'enabled': True,
                'description': description,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

            logger.info(f"Added job {job_id} with schedule {cron_expression}")
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {str(e)}")

    def _run_sync_job(self):
        """
        Run the sync job - directly calling the sync_metadata function
        """
        try:
            logger.info("Executing hourly sync job")

            # Get the channel ID and other required parameters
            channel_id = get_channel_id()
            api_key = get_youtube_api_key()
            repository_dir = get_repository_dir()

            if not api_key:
                logger.error("No YouTube API key found in config")
                return

            # Call the sync_metadata function directly
            result = sync_metadata(
                api_key=api_key,
                channel_id=channel_id,
                channel_title="Einundzwanzig",
                output_dir=repository_dir,
                max_videos=5,
                force_refresh=True
            )

            if result:
                logger.info("Hourly sync job completed successfully")
            else:
                logger.error("Hourly sync job failed")

            # Update next run time
            job = self.scheduler.get_job('hourly_sync')
            if job and job.next_run_time:
                self.jobs['hourly_sync']['next_run'] = job.next_run_time.isoformat()

        except Exception as e:
            logger.error(f"Error executing hourly sync job: {str(e)}")

    def _run_download_job(self):
        """
        Run the download job - directly calling the download_video function
        """
        try:
            logger.info("Executing daily download job")

            # Get the channel ID and other required parameters
            channel_id = get_channel_id()
            repository_dir = get_repository_dir()

            # Get the videos directory for this channel
            videos_dir = os.path.join(repository_dir, "Einundzwanzig", "videos")

            # Find the oldest video without download
            from ..metadata.list import list_videos
            videos, _ = list_videos(videos_dir, show_downloaded=False, show_not_downloaded=True)

            if not videos:
                logger.info("No pending videos to download")
                return

            # Get the first (oldest) video
            video = videos[0]
            video_id = video['video_id']

            # Get the default video quality
            quality = get_default_video_quality()

            # Call the download_video function directly
            result = download_video(
                video_id=video_id,
                videos_dir=videos_dir,
                quality=quality
            )

            if result:
                logger.info(f"Downloaded video {video_id} successfully")
            else:
                logger.error(f"Failed to download video {video_id}")

            # Update next run time
            job = self.scheduler.get_job('daily_download')
            if job and job.next_run_time:
                self.jobs['daily_download']['next_run'] = job.next_run_time.isoformat()

        except Exception as e:
            logger.error(f"Error executing daily download job: {str(e)}")

    def _add_weekly_nostr_job(self):
        """
        Add weekly nostr posting job to the scheduler
        """
        job_id = 'weekly_nostr'
        cron_expression = '0 3 * * 0'  # Every Sunday at 3 AM
        description = 'Post the oldest pending video to Nostr every week'

        try:
            # Add the job to the scheduler
            job = self.scheduler.add_job(
                self._run_nostr_job,
                trigger=CronTrigger.from_crontab(cron_expression),
                id=job_id,
                replace_existing=True
            )

            # Store job metadata
            self.jobs[job_id] = {
                'id': job_id,
                'command': 'nostr',
                'args': ['--oldest'],
                'schedule': cron_expression,
                'enabled': True,
                'description': description,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

            logger.info(f"Added job {job_id} with schedule {cron_expression}")
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {str(e)}")

    def _run_nostr_job(self):
        """
        Run the nostr job - directly calling the post_to_nostr function
        """
        try:
            logger.info("Executing weekly nostr posting job")

            # Get the required parameters
            repository_dir = get_repository_dir()

            # Get the videos directory for this channel
            videos_dir = os.path.join(repository_dir, "Einundzwanzig", "videos")

            # Find videos that have been downloaded but not posted to Nostr
            from ..metadata.list import list_videos
            videos, _ = list_videos(videos_dir)

            # Filter for videos that are downloaded but don't have Nostr posts
            pending_videos = []
            for video in videos:
                if video.get('downloaded'):
                    # Check if the video has been posted to Nostr
                    has_nostr = False
                    if 'platforms' in video and 'nostr' in video.get('platforms', {}):
                        # Check if there are any posts in the nostr platform
                        nostr_data = video['platforms']['nostr']
                        if 'posts' in nostr_data and len(nostr_data['posts']) > 0:
                            has_nostr = True
                        # For backward compatibility with old metadata format
                        elif 'event_id' in nostr_data:
                            has_nostr = True

                    if not has_nostr:
                        pending_videos.append(video)

            if not pending_videos:
                logger.info("No pending videos to post to Nostr")
                return

            # Get the first (oldest) video
            video = pending_videos[0]
            video_id = video['video_id']

            # Call the post_to_nostr function directly
            result = post_to_nostr(
                video_id=video_id,
                channel_id="UCxSRxq14XIoMbFDEjMOPU5Q",  # Hardcoded channel ID
                debug=False
            )

            if result:
                logger.info(f"Posted video {video_id} to Nostr successfully")
            else:
                logger.error(f"Failed to post video {video_id} to Nostr")

            # Update next run time
            job = self.scheduler.get_job('weekly_nostr')
            if job and job.next_run_time:
                self.jobs['weekly_nostr']['next_run'] = job.next_run_time.isoformat()

        except Exception as e:
            logger.error(f"Error executing weekly nostr posting job: {str(e)}")

    def _add_regular_sync_job(self):
        """
        Add regular sync job to the scheduler (every 5 minutes)
        """
        job_id = 'regular_sync'
        cron_expression = '*/5 * * * *'  # Every 5 minutes
        description = 'Sync metadata for new videos every 5 minutes'

        try:
            # Add the job to the scheduler
            job = self.scheduler.add_job(
                self._run_regular_sync_job,
                trigger=CronTrigger.from_crontab(cron_expression),
                id=job_id,
                replace_existing=True
            )

            # Store job metadata
            self.jobs[job_id] = {
                'id': job_id,
                'command': 'sync',
                'args': ['--max-videos', '10'],
                'schedule': cron_expression,
                'enabled': True,
                'description': description,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

            logger.info(f"Added job {job_id} with schedule {cron_expression}")
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {str(e)}")

    def _run_regular_sync_job(self):
        """
        Run the regular sync job - directly calling the sync_metadata function
        """
        try:
            logger.info("Executing regular sync job")

            # Get the channel ID and other required parameters
            channel_id = get_channel_id()
            api_key = get_youtube_api_key()
            repository_dir = get_repository_dir()

            if not api_key:
                logger.error("No YouTube API key found in config")
                return

            # Call the sync_metadata function directly
            result = sync_metadata(
                api_key=api_key,
                channel_id=channel_id,
                channel_title="Einundzwanzig",
                output_dir=repository_dir,
                max_videos=10,
                force_refresh=False  # Regular sync without force refresh
            )

            if result:
                logger.info("Regular sync job completed successfully")
            else:
                logger.error("Regular sync job failed")

            # Update next run time
            job = self.scheduler.get_job('regular_sync')
            if job and job.next_run_time:
                self.jobs['regular_sync']['next_run'] = job.next_run_time.isoformat()

        except Exception as e:
            logger.error(f"Error executing regular sync job: {str(e)}")

    def _add_regular_download_job(self):
        """
        Add regular download job to the scheduler (every 5 minutes)
        """
        job_id = 'regular_download'
        cron_expression = '*/5 * * * *'  # Every 5 minutes
        description = 'Download 5 pending videos every 5 minutes'

        try:
            # Add the job to the scheduler
            job = self.scheduler.add_job(
                self._run_regular_download_job,
                trigger=CronTrigger.from_crontab(cron_expression),
                id=job_id,
                replace_existing=True
            )

            # Store job metadata
            self.jobs[job_id] = {
                'id': job_id,
                'command': 'download',
                'args': ['--max-videos', '5'],
                'schedule': cron_expression,
                'enabled': True,
                'description': description,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

            logger.info(f"Added job {job_id} with schedule {cron_expression}")
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {str(e)}")

    def _run_regular_download_job(self):
        """
        Run the regular download job - download up to 5 videos
        """
        try:
            logger.info("Executing regular download job")

            # Get the required parameters
            repository_dir = get_repository_dir()

            # Get the videos directory for this channel
            videos_dir = os.path.join(repository_dir, "Einundzwanzig", "videos")

            # Get the default video quality
            quality = get_default_video_quality()

            # Find videos that need to be downloaded
            from ..metadata.list import list_videos
            videos, _ = list_videos(videos_dir, show_downloaded=False, show_not_downloaded=True)

            if not videos:
                logger.info("No pending videos to download")
                return

            # Download up to 5 videos
            videos_downloaded = 0
            max_videos = 5

            for i in range(min(max_videos, len(videos))):
                video = videos[i]
                video_id = video['video_id']

                # Call the download_video function directly
                result = download_video(
                    video_id=video_id,
                    videos_dir=videos_dir,
                    quality=quality
                )

                if result:
                    logger.info(f"Downloaded video {video_id} successfully")
                    videos_downloaded += 1
                else:
                    logger.error(f"Failed to download video {video_id}")

            logger.info(f"Regular download job completed: {videos_downloaded} videos downloaded")

            # Update next run time
            job = self.scheduler.get_job('regular_download')
            if job and job.next_run_time:
                self.jobs['regular_download']['next_run'] = job.next_run_time.isoformat()

        except Exception as e:
            logger.error(f"Error executing regular download job: {str(e)}")

    def _add_regular_nostrmedia_job(self):
        """
        Add regular nostrmedia upload job to the scheduler (every 5 minutes)
        """
        job_id = 'regular_nostrmedia'
        cron_expression = '*/5 * * * *'  # Every 5 minutes
        description = 'Upload pending videos to nostrmedia every 5 minutes'

        try:
            # Add the job to the scheduler
            job = self.scheduler.add_job(
                self._run_regular_nostrmedia_job,
                trigger=CronTrigger.from_crontab(cron_expression),
                id=job_id,
                replace_existing=True
            )

            # Store job metadata
            self.jobs[job_id] = {
                'id': job_id,
                'command': 'nostrmedia',
                'args': ['--oldest'],
                'schedule': cron_expression,
                'enabled': True,
                'description': description,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            }

            logger.info(f"Added job {job_id} with schedule {cron_expression}")
        except Exception as e:
            logger.error(f"Error adding job {job_id}: {str(e)}")

    def _run_regular_nostrmedia_job(self):
        """
        Run the regular nostrmedia upload job
        """
        try:
            logger.info("Executing regular nostrmedia upload job")

            # Get the required parameters
            repository_dir = get_repository_dir()

            # Get the videos directory for this channel
            videos_dir = os.path.join(repository_dir, "Einundzwanzig", "videos")

            # Find videos that have been downloaded but not uploaded to nostrmedia
            from ..metadata.list import list_videos
            videos, _ = list_videos(videos_dir)

            # Filter for videos that are downloaded but don't have nostrmedia URL
            pending_videos = []
            for video in videos:
                if video.get('downloaded') and not video.get('platforms', {}).get('nostrmedia', {}).get('url'):
                    pending_videos.append(video)

            if not pending_videos:
                logger.info("No pending videos to upload to nostrmedia")
                return

            # Get the first (oldest) video
            video = pending_videos[0]
            video_id = video['video_id']

            # Get the video file path
            video_dir = os.path.join(videos_dir, video_id)
            youtube_dir = os.path.join(video_dir, "youtube")

            # Find the video file
            video_files = [f for f in os.listdir(youtube_dir) if f.endswith(".mp4")] if os.path.exists(youtube_dir) else []

            if not video_files:
                logger.error(f"No video files found for {video_id}")
                return

            video_path = os.path.join(youtube_dir, video_files[0])

            # Call the upload_to_nostrmedia function directly
            result = upload_to_nostrmedia(
                file_path=video_path,
                debug=False
            )

            if result and result.get('success'):
                logger.info(f"Uploaded video {video_id} to nostrmedia successfully")

                # Update the metadata
                metadata_path = os.path.join(video_dir, "metadata.json")
                if os.path.exists(metadata_path):
                    from ..utils.filesystem import load_json_file, save_json_file
                    metadata = load_json_file(metadata_path)

                    # Update the metadata with nostrmedia URL
                    metadata['platforms'] = metadata.get('platforms', {})
                    metadata['platforms']['nostrmedia'] = {
                        'url': result.get('url'),
                        'uploaded_at': datetime.now().isoformat()
                    }
                    save_json_file(metadata_path, metadata)
            else:
                error_msg = result.get('error') if result else 'Unknown error'
                logger.error(f"Failed to upload video {video_id} to nostrmedia: {error_msg}")

            # Update next run time
            job = self.scheduler.get_job('regular_nostrmedia')
            if job and job.next_run_time:
                self.jobs['regular_nostrmedia']['next_run'] = job.next_run_time.isoformat()

        except Exception as e:
            logger.error(f"Error executing regular nostrmedia upload job: {str(e)}")

    def _log_job_schedule(self):
        """
        Log the next run times for all jobs
        """
        if not self.jobs:
            logger.info("No scheduled jobs")
            return

        logger.info("Scheduled jobs:")
        for job_id, job_info in self.jobs.items():
            next_run = job_info.get('next_run', 'Not scheduled')
            logger.info(f"  - {job_id}: {job_info['description']} (Next run: {next_run})")

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Get all jobs

        Returns:
            List of job metadata
        """
        # Update next run times before returning
        for job_id in self.jobs:
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                self.jobs[job_id]['next_run'] = job.next_run_time.isoformat()

        return list(self.jobs.values())

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a job by ID

        Args:
            job_id: ID of the job

        Returns:
            Job metadata or None if not found
        """
        # Update next run time before returning
        if job_id in self.jobs:
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                self.jobs[job_id]['next_run'] = job.next_run_time.isoformat()

        return self.jobs.get(job_id)

    def shutdown(self):
        """
        Shutdown the scheduler
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

#!/usr/bin/env python3
"""
NosVid Updater

This script watches for the update trigger file and updates NosVid when needed.
It should be run as a separate service from NosVid.
It uses a simple deploy key approach for authentication.
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

# Configuration
UPDATE_TRIGGER_FILE = "/tmp/nosvid_update_needed"
CHECK_INTERVAL = 60  # Check for updates every 60 seconds
NOSVID_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(NOSVID_DIR, "backups")
VENV_PATH = os.path.join(NOSVID_DIR, "venv")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(NOSVID_DIR, "updater.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("updater")


def stop_decdata():
    """
    Stop the DecData service
    """
    logger.info("Stopping DecData service")
    try:
        subprocess.run(
            "sudo systemctl stop decdata.service",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait a moment to ensure it's stopped
        time.sleep(5)

        # Check if it's really stopped
        status_result = subprocess.run(
            "systemctl is-active decdata.service",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if "inactive" in status_result.stdout:
            logger.info("DecData service stopped successfully")
            return True
        else:
            logger.warning("DecData service may still be running")
            return False
    except Exception as e:
        logger.error(f"Error stopping DecData service: {e}")
        return False


def start_decdata():
    """
    Start the DecData service
    """
    logger.info("Starting DecData service")
    try:
        subprocess.run(
            "sudo systemctl start decdata.service",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait a moment to ensure it's started
        time.sleep(5)

        # Check if it's really started
        status_result = subprocess.run(
            "systemctl is-active decdata.service",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if "active" in status_result.stdout:
            logger.info("DecData service started successfully")
            return True
        else:
            logger.error("Failed to start DecData service")
            return False
    except Exception as e:
        logger.error(f"Error starting DecData service: {e}")
        return False


def create_backup():
    """
    Create a backup of the current NosVid installation
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"nosvid_backup_{timestamp}")

    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Create a backup of the current code (excluding venv and backups)
    logger.info(f"Creating backup at {backup_path}")
    try:
        # Use rsync to copy files, excluding venv and backups
        result = subprocess.run(
            f"rsync -a --exclude='venv' --exclude='backups' {NOSVID_DIR}/ {backup_path}/",
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.info("Backup created successfully")
        return True
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False


def stop_nosvid():
    """
    Stop the NosVid service
    """
    logger.info("Stopping NosVid service")
    try:
        result = subprocess.run(
            "sudo systemctl stop nosvid.service",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait a moment to ensure it's stopped
        time.sleep(5)

        # Check if it's really stopped
        status_result = subprocess.run(
            "systemctl is-active nosvid.service",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if "inactive" in status_result.stdout:
            logger.info("NosVid service stopped successfully")
            return True
        else:
            logger.warning("NosVid service may still be running")
            return False
    except Exception as e:
        logger.error(f"Error stopping NosVid service: {e}")
        return False


def start_nosvid():
    """
    Start the NosVid service
    """
    logger.info("Starting NosVid service")
    try:
        result = subprocess.run(
            "sudo systemctl start nosvid.service",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait a moment to ensure it's started
        time.sleep(5)

        # Check if it's really started
        status_result = subprocess.run(
            "systemctl is-active nosvid.service",
            shell=True,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if "active" in status_result.stdout:
            logger.info("NosVid service started successfully")
            return True
        else:
            logger.error("Failed to start NosVid service")
            return False
    except Exception as e:
        logger.error(f"Error starting NosVid service: {e}")
        return False


def restart_service(service_name):
    """
    Restart a systemd service

    Args:
        service_name: Name of the service to restart

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Restarting service: {service_name}")
        result = subprocess.run(
            ["sudo", "systemctl", "restart", service_name],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Failed to restart service: {result.stderr}")
            return False

        logger.info(f"Successfully restarted service: {service_name}")
        return True

    except Exception as e:
        logger.error(f"Error restarting service: {e}")
        return False


def process_update():
    """
    Process the update trigger file and update NosVid and DecData
    """
    logger.info("Processing update")

    # Read the trigger file
    try:
        with open(UPDATE_TRIGGER_FILE, "r") as f:
            trigger_content = f.read()
        logger.info(f"Trigger file content:\n{trigger_content}")
    except Exception as e:
        logger.error(f"Error reading trigger file: {e}")

    # Create a backup
    if not create_backup():
        logger.error("Backup failed, aborting update")
        return False

    # Stop both services
    logger.info("Stopping services...")
    nosvid_stopped = stop_nosvid()
    decdata_stopped = stop_decdata()

    if not nosvid_stopped:
        logger.warning("Failed to stop NosVid, continuing anyway")

    if not decdata_stopped:
        logger.warning("Failed to stop DecData, continuing anyway")

    # Update the repository
    try:
        # Pull the latest code using the deploy key (which should be configured in the system)
        logger.info("Pulling latest changes")
        result = subprocess.run(
            ["git", "pull"], cwd=NOSVID_DIR, capture_output=True, text=True
        )

        if result.returncode != 0:
            logger.error(f"Failed to pull changes: {result.stderr}")
            # Try to restart services
            start_nosvid()
            start_decdata()
            return False

        logger.info(f"Successfully pulled changes: {result.stdout}")

        # Update dependencies
        logger.info("Updating dependencies")
        result = subprocess.run(
            [f"{VENV_PATH}/bin/pip", "install", "-e", NOSVID_DIR],
            cwd=NOSVID_DIR,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Failed to update dependencies: {result.stderr}")
            # Try to restart services
            start_nosvid()
            start_decdata()
            return False

        # Ensure yt-dlp is installed
        logger.info("Ensuring yt-dlp is installed")
        subprocess.run(
            [f"{VENV_PATH}/bin/pip", "install", "yt-dlp"],
            cwd=NOSVID_DIR,
            capture_output=True,
            text=True,
        )

        # Create symlink for yt-dlp if it doesn't exist
        logger.info("Checking yt-dlp symlink")
        if not os.path.exists("/usr/local/bin/yt-dlp"):
            logger.info("Creating symlink for yt-dlp")
            subprocess.run(
                [
                    "sudo",
                    "ln",
                    "-sf",
                    f"{VENV_PATH}/bin/yt-dlp",
                    "/usr/local/bin/yt-dlp",
                ],
                capture_output=True,
                text=True,
            )
    except Exception as e:
        logger.error(f"Error updating repository: {e}")
        # Try to restart services
        start_nosvid()
        start_decdata()
        return False

    # Start both services
    logger.info("Starting services...")
    nosvid_started = start_nosvid()
    decdata_started = start_decdata()

    if not nosvid_started:
        logger.error("Failed to start NosVid after update")
        return False

    if not decdata_started:
        logger.error("Failed to start DecData after update")
        return False

    logger.info("Update completed successfully")
    return True


def check_for_updates():
    """
    Check if an update is needed
    """
    if os.path.exists(UPDATE_TRIGGER_FILE):
        logger.info(f"Found update trigger file: {UPDATE_TRIGGER_FILE}")

        # Process the update
        success = process_update()

        # Remove the trigger file
        try:
            os.remove(UPDATE_TRIGGER_FILE)
            logger.info("Removed update trigger file")
        except Exception as e:
            logger.error(f"Error removing trigger file: {e}")

        return success

    return False


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description="NosVid Updater")
    parser.add_argument(
        "--check-interval",
        type=int,
        default=CHECK_INTERVAL,
        help=f"Check interval in seconds (default: {CHECK_INTERVAL})",
    )
    args = parser.parse_args()

    logger.info("Starting NosVid updater")

    while True:
        try:
            check_for_updates()
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")

        time.sleep(args.check_interval)


if __name__ == "__main__":
    main()

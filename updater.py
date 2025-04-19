#!/usr/bin/env python3
"""
NosVid Updater

This script watches for the update trigger file and updates NosVid when needed.
It should be run as a separate service from NosVid.
"""

import os
import sys
import time
import logging
import subprocess
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("updater.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("updater")

# Configuration
UPDATE_TRIGGER_FILE = "/tmp/nosvid_update_needed"
CHECK_INTERVAL = 60  # Check for updates every 60 seconds
NOSVID_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(NOSVID_DIR, "backups")
VENV_PATH = os.path.join(NOSVID_DIR, "venv")

def run_command(command, cwd=None):
    """Run a shell command and return the output"""
    logger.info(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd
        )
        logger.info(f"Command output: {result.stdout}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return False, e.stderr

def create_backup():
    """Create a backup of the current NosVid installation"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"nosvid_backup_{timestamp}")

    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Create a backup of the current code (excluding venv and backups)
    logger.info(f"Creating backup at {backup_path}")
    try:
        # Use rsync to copy files, excluding venv and backups
        run_command(
            f"rsync -a --exclude='venv' --exclude='backups' {NOSVID_DIR}/ {backup_path}/"
        )
        logger.info("Backup created successfully")
        return True
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False

def stop_nosvid():
    """Stop the NosVid service"""
    logger.info("Stopping NosVid service")
    success, _ = run_command("sudo systemctl stop nosvid.service")

    # Wait a moment to ensure it's stopped
    time.sleep(5)

    # Check if it's really stopped
    _, status = run_command("systemctl is-active nosvid.service")
    if "inactive" in status:
        logger.info("NosVid service stopped successfully")
        return True
    else:
        logger.warning("NosVid service may still be running")
        return False

def update_nosvid():
    """Update NosVid from GitHub"""
    logger.info("Updating NosVid from GitHub")

    # Pull the latest code
    success, _ = run_command("git pull", cwd=NOSVID_DIR)
    if not success:
        logger.error("Failed to pull latest code")
        return False

    # Update dependencies
    logger.info("Updating dependencies")
    success, _ = run_command(f"{VENV_PATH}/bin/pip install -e {NOSVID_DIR}", cwd=NOSVID_DIR)
    if not success:
        logger.error("Failed to update dependencies")
        return False

    # Ensure yt-dlp is installed
    logger.info("Ensuring yt-dlp is installed")
    success, _ = run_command(f"{VENV_PATH}/bin/pip install yt-dlp", cwd=NOSVID_DIR)
    if not success:
        logger.warning("Failed to install yt-dlp via pip, but continuing")

    # Create symlink for yt-dlp if it doesn't exist
    logger.info("Checking yt-dlp symlink")
    if not os.path.exists("/usr/local/bin/yt-dlp"):
        logger.info("Creating symlink for yt-dlp")
        success, _ = run_command(f"sudo ln -sf {VENV_PATH}/bin/yt-dlp /usr/local/bin/yt-dlp")
        if not success:
            logger.warning("Failed to create symlink for yt-dlp, but continuing")

    logger.info("NosVid updated successfully")
    return True

def start_nosvid():
    """Start the NosVid service"""
    logger.info("Starting NosVid service")
    success, _ = run_command("sudo systemctl start nosvid.service")

    # Wait a moment to ensure it's started
    time.sleep(5)

    # Check if it's really started
    _, status = run_command("systemctl is-active nosvid.service")
    if "active" in status:
        logger.info("NosVid service started successfully")
        return True
    else:
        logger.error("Failed to start NosVid service")
        return False

def process_update():
    """Process the update trigger file and update NosVid"""
    logger.info("Processing update")

    # Read the trigger file
    try:
        with open(UPDATE_TRIGGER_FILE, 'r') as f:
            trigger_content = f.read()
        logger.info(f"Trigger file content:\n{trigger_content}")
    except Exception as e:
        logger.error(f"Error reading trigger file: {e}")

    # Create a backup
    if not create_backup():
        logger.error("Backup failed, aborting update")
        return False

    # Stop NosVid
    if not stop_nosvid():
        logger.warning("Failed to stop NosVid, continuing anyway")

    # Update NosVid
    if not update_nosvid():
        logger.error("Update failed, attempting to restart NosVid")
        start_nosvid()
        return False

    # Start NosVid
    if not start_nosvid():
        logger.error("Failed to start NosVid after update")
        return False

    logger.info("Update completed successfully")
    return True

def check_for_updates():
    """Check if an update is needed"""
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
    """Main function"""
    logger.info("Starting NosVid updater")

    while True:
        try:
            check_for_updates()
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Updater stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Updater crashed: {e}")
        sys.exit(1)

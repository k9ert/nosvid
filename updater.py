#!/usr/bin/env python3
"""
NosVid Updater

This script watches for the update trigger file and updates NosVid when needed.
It should be run as a separate service from NosVid.
It uses GitHub App authentication with PEM keys to pull the latest changes.
"""

import os
import sys
import time
import json
import logging
import subprocess
import requests
import jwt
from datetime import datetime, timedelta
import argparse

# Configuration
UPDATE_TRIGGER_FILE = "/tmp/nosvid_update_needed"
CHECK_INTERVAL = 60  # Check for updates every 60 seconds
NOSVID_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(NOSVID_DIR, "backups")
VENV_PATH = os.path.join(NOSVID_DIR, "venv")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(NOSVID_DIR, "updater.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('updater')

class GitHubAppAuth:
    """
    GitHub App authentication helper
    """
    def __init__(self, app_id, private_key_path, installation_id):
        """
        Initialize the GitHub App authentication

        Args:
            app_id: GitHub App ID
            private_key_path: Path to the private key file (.pem)
            installation_id: Installation ID for the repository
        """
        self.app_id = app_id
        self.private_key_path = private_key_path
        self.installation_id = installation_id
        self.access_token = None
        self.token_expires_at = None

    def _generate_jwt(self):
        """
        Generate a JWT for GitHub App authentication

        Returns:
            JWT token string
        """
        now = datetime.now()
        expiration = now + timedelta(minutes=10)  # Token valid for 10 minutes

        with open(self.private_key_path, 'rb') as key_file:
            private_key = key_file.read()

        payload = {
            'iat': int(now.timestamp()),
            'exp': int(expiration.timestamp()),
            'iss': self.app_id
        }

        token = jwt.encode(payload, private_key, algorithm='RS256')
        return token

    def get_access_token(self):
        """
        Get an access token for the GitHub App installation

        Returns:
            Access token string
        """
        # Check if we have a valid token
        now = datetime.now()
        if self.access_token and self.token_expires_at and now < self.token_expires_at:
            return self.access_token

        # Generate a new token
        jwt_token = self._generate_jwt()

        response = requests.post(
            f"https://api.github.com/app/installations/{self.installation_id}/access_tokens",
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"Bearer {jwt_token}"
            }
        )

        if response.status_code != 201:
            logger.error(f"Failed to get access token: {response.status_code} {response.text}")
            return None

        data = response.json()
        self.access_token = data['token']
        # Token expires in 1 hour, but we'll refresh it after 50 minutes
        self.token_expires_at = now + timedelta(minutes=50)

        return self.access_token

class RepositoryUpdater:
    """
    Repository updater
    """
    def __init__(self, repo_path, repo_owner, repo_name, auth):
        """
        Initialize the repository updater

        Args:
            repo_path: Path to the local repository
            repo_owner: GitHub repository owner (username or organization)
            repo_name: GitHub repository name
            auth: GitHubAppAuth instance
        """
        self.repo_path = repo_path
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.auth = auth

    def update(self):
        """
        Update the repository by pulling the latest changes

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get access token
            access_token = self.auth.get_access_token()
            if not access_token:
                logger.error("Failed to get access token")
                return False

            # Construct the remote URL with the access token
            remote_url = f"https://{access_token}@github.com/{self.repo_owner}/{self.repo_name}.git"

            # Change to the repository directory
            os.chdir(self.repo_path)

            # Pull the latest changes
            logger.info(f"Pulling latest changes for {self.repo_owner}/{self.repo_name}")
            result = subprocess.run(
                ["git", "pull", remote_url],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to pull changes: {result.stderr}")
                return False

            logger.info(f"Successfully pulled changes: {result.stdout}")
            return True

        except Exception as e:
            logger.error(f"Error updating repository: {e}")
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
            text=True
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
            text=True
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
            text=True
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
            text=True
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
            text=True
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
            text=True
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
    Process the update trigger file and update NosVid
    """
    logger.info("Processing update")

    # Read the trigger file
    try:
        with open(UPDATE_TRIGGER_FILE, 'r') as f:
            trigger_content = f.read()
        logger.info(f"Trigger file content:\n{trigger_content}")
    except Exception as e:
        logger.error(f"Error reading trigger file: {e}")

    # Load configuration
    config_path = os.path.join(NOSVID_DIR, "updater_config.json")

    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Creating example configuration file...")

        example_config = {
            "github_app": {
                "app_id": "YOUR_APP_ID",
                "private_key_path": "/path/to/your/private_key.pem",
                "installation_id": "YOUR_INSTALLATION_ID"
            },
            "repository": {
                "owner": "YOUR_GITHUB_USERNAME_OR_ORG",
                "name": "nosvid"
            }
        }

        with open(config_path, 'w') as f:
            json.dump(example_config, f, indent=2)

        logger.error(f"Example configuration file created at {config_path}")
        logger.error("Please edit the configuration file and run the updater again.")
        return False

    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration file: {e}")
        return False

    # Create GitHub App authentication
    try:
        auth = GitHubAppAuth(
            app_id=config['github_app']['app_id'],
            private_key_path=config['github_app']['private_key_path'],
            installation_id=config['github_app']['installation_id']
        )
    except Exception as e:
        logger.error(f"Error creating GitHub App authentication: {e}")
        return False

    # Create a backup
    if not create_backup():
        logger.error("Backup failed, aborting update")
        return False

    # Stop NosVid
    if not stop_nosvid():
        logger.warning("Failed to stop NosVid, continuing anyway")

    # Update NosVid
    try:
        # Get access token
        access_token = auth.get_access_token()
        if not access_token:
            logger.error("Failed to get access token")
            start_nosvid()  # Try to restart NosVid
            return False

        # Construct the remote URL with the access token
        repo_owner = config['repository']['owner']
        repo_name = config['repository']['name']
        remote_url = f"https://{access_token}@github.com/{repo_owner}/{repo_name}.git"

        # Pull the latest code
        logger.info(f"Pulling latest changes for {repo_owner}/{repo_name}")
        result = subprocess.run(
            ["git", "pull", remote_url],
            cwd=NOSVID_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Failed to pull changes: {result.stderr}")
            start_nosvid()  # Try to restart NosVid
            return False

        logger.info(f"Successfully pulled changes: {result.stdout}")

        # Update dependencies
        logger.info("Updating dependencies")
        result = subprocess.run(
            [f"{VENV_PATH}/bin/pip", "install", "-e", NOSVID_DIR],
            cwd=NOSVID_DIR,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Failed to update dependencies: {result.stderr}")
            start_nosvid()  # Try to restart NosVid
            return False

        # Ensure yt-dlp is installed
        logger.info("Ensuring yt-dlp is installed")
        subprocess.run(
            [f"{VENV_PATH}/bin/pip", "install", "yt-dlp"],
            cwd=NOSVID_DIR,
            capture_output=True,
            text=True
        )

        # Create symlink for yt-dlp if it doesn't exist
        logger.info("Checking yt-dlp symlink")
        if not os.path.exists("/usr/local/bin/yt-dlp"):
            logger.info("Creating symlink for yt-dlp")
            subprocess.run(
                ["sudo", "ln", "-sf", f"{VENV_PATH}/bin/yt-dlp", "/usr/local/bin/yt-dlp"],
                capture_output=True,
                text=True
            )
    except Exception as e:
        logger.error(f"Error updating NosVid: {e}")
        start_nosvid()  # Try to restart NosVid
        return False

    # Start NosVid
    if not start_nosvid():
        logger.error("Failed to start NosVid after update")
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
    parser = argparse.ArgumentParser(description='NosVid Updater')
    parser.add_argument('--check-interval', type=int, default=CHECK_INTERVAL,
                        help=f'Check interval in seconds (default: {CHECK_INTERVAL})')
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

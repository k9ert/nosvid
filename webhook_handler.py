#!/usr/bin/env python3
"""
GitHub webhook handler for NosVid

This script runs a simple HTTP server that listens for GitHub webhook events
and triggers updates when a push is made to the main branch.
"""

import os
import sys
import json
import hmac
import hashlib
import http.server
import socketserver
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("webhook.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("webhook")

# Configuration
PORT = 9000  # Port to listen on
UPDATE_TRIGGER_FILE = "/tmp/nosvid_update_needed"
GITHUB_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")  # Set this in your environment
BRANCH_TO_WATCH = "main"  # Branch to watch for changes

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def _send_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode())

    def do_POST(self):
        # Check if this is the webhook endpoint
        if self.path != "/webhook":
            self._send_response(404, "Not Found")
            return

        # Get content length
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self._send_response(400, "Empty request")
            return

        # Read and parse the request body
        post_data = self.rfile.read(content_length)
        
        # Verify signature if secret is set
        if GITHUB_SECRET:
            signature = self.headers.get('X-Hub-Signature-256')
            if not signature:
                logger.warning("No signature provided")
                self._send_response(403, "Forbidden")
                return
                
            computed_signature = 'sha256=' + hmac.new(
                GITHUB_SECRET.encode(),
                post_data,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, computed_signature):
                logger.warning("Invalid signature")
                self._send_response(403, "Forbidden")
                return
        
        # Parse the JSON payload
        try:
            payload = json.loads(post_data.decode())
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload")
            self._send_response(400, "Invalid JSON")
            return
        
        # Check if this is a push event
        event_type = self.headers.get('X-GitHub-Event')
        if event_type != 'push':
            logger.info(f"Ignoring non-push event: {event_type}")
            self._send_response(200, "OK")
            return
        
        # Check if the push is to the branch we're watching
        ref = payload.get('ref')
        if not ref or ref != f"refs/heads/{BRANCH_TO_WATCH}":
            logger.info(f"Ignoring push to branch: {ref}")
            self._send_response(200, "OK")
            return
        
        # Get the repository name
        repo_name = payload.get('repository', {}).get('name', 'unknown')
        
        # Get the commit information
        commits = payload.get('commits', [])
        commit_messages = [commit.get('message', '').split('\n')[0] for commit in commits]
        commit_count = len(commits)
        
        logger.info(f"Received push to {BRANCH_TO_WATCH} in {repo_name} with {commit_count} commits")
        for i, msg in enumerate(commit_messages):
            logger.info(f"  Commit {i+1}: {msg}")
        
        # Create the update trigger file
        try:
            with open(UPDATE_TRIGGER_FILE, 'w') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"Update triggered at {timestamp}\n")
                f.write(f"Repository: {repo_name}\n")
                f.write(f"Branch: {BRANCH_TO_WATCH}\n")
                f.write(f"Commits: {commit_count}\n")
                for i, msg in enumerate(commit_messages):
                    f.write(f"Commit {i+1}: {msg}\n")
            
            logger.info(f"Created update trigger file: {UPDATE_TRIGGER_FILE}")
            self._send_response(200, "Update triggered")
        except Exception as e:
            logger.error(f"Error creating update trigger file: {e}")
            self._send_response(500, "Internal Server Error")
            return

def run_server():
    try:
        with socketserver.TCPServer(("", PORT), WebhookHandler) as httpd:
            logger.info(f"Starting webhook server on port {PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down webhook server")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error starting webhook server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()

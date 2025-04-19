# NosVid Deployment Guide

This guide explains how to deploy NosVid on a VPS with automatic startup and GitHub webhook integration for updates.

## Prerequisites

- A VPS running Ubuntu or Debian
- Git installed
- Python 3.8+ installed
- Sudo access

## Installation

1. Clone the NosVid repository:
   ```bash
   git clone https://github.com/yourusername/nosvid.git
   cd nosvid
   ```

2. Run the installation script:
   ```bash
   ./install_service.sh
   ```

   This script will:
   - Create a Python virtual environment
   - Install NosVid and its dependencies
   - Install yt-dlp
   - Set up systemd services for NosVid, webhook handler, and updater
   - Start all services

3. Configure your `config.yaml` file with your API keys and other settings.

## Services

The installation creates three systemd services:

1. **nosvid.service**: The main NosVid application
2. **nosvid-webhook.service**: Listens for GitHub webhook events
3. **nosvid-updater.service**: Watches for update trigger files and updates NosVid

## GitHub Webhook Setup

1. Go to your GitHub repository settings
2. Navigate to Webhooks > Add webhook
3. Set the Payload URL to `http://your-server-ip:9000/webhook`
4. Set the Content type to `application/json`
5. Set the Secret to the same value you entered during installation
6. Select "Just the push event"
7. Make sure "Active" is checked
8. Click "Add webhook"

## Managing Services

### Check Service Status

```bash
# Check NosVid status
sudo systemctl status nosvid.service

# Check webhook handler status
sudo systemctl status nosvid-webhook.service

# Check updater status
sudo systemctl status nosvid-updater.service
```

### View Logs

```bash
# View NosVid logs
sudo journalctl -u nosvid.service -f

# View webhook handler logs
sudo journalctl -u nosvid-webhook.service -f

# View updater logs
sudo journalctl -u nosvid-updater.service -f
```

### Restart Services

```bash
# Restart NosVid
sudo systemctl restart nosvid.service

# Restart webhook handler
sudo systemctl restart nosvid-webhook.service

# Restart updater
sudo systemctl restart nosvid-updater.service
```

## Troubleshooting

### yt-dlp Not Found

If you see errors like `[Errno 2] No such file or directory: 'yt-dlp'`:

1. Install yt-dlp manually:
   ```bash
   sudo pip install yt-dlp
   ```

2. Restart the NosVid service:
   ```bash
   sudo systemctl restart nosvid.service
   ```

### Webhook Not Working

1. Check the webhook handler logs:
   ```bash
   sudo journalctl -u nosvid-webhook.service -f
   ```

2. Verify your GitHub webhook settings
3. Make sure port 9000 is open in your firewall

### Updates Not Applied

1. Check the updater logs:
   ```bash
   sudo journalctl -u nosvid-updater.service -f
   ```

2. Manually trigger an update by creating the trigger file:
   ```bash
   echo "Manual update" > /tmp/nosvid_update_needed
   ```

3. Wait for the updater to detect the file (should be within 60 seconds)

## Manual Update

If you need to update NosVid manually:

1. Stop the NosVid service:
   ```bash
   sudo systemctl stop nosvid.service
   ```

2. Pull the latest code:
   ```bash
   cd /path/to/nosvid
   git pull
   ```

3. Update dependencies:
   ```bash
   ./venv/bin/pip install -e .
   ```

4. Start the NosVid service:
   ```bash
   sudo systemctl start nosvid.service
   ```

# NosVid Management Commands

This document provides essential commands for managing the NosVid application on your server.

## Service Management

### Start, Stop, and Restart the NosVid Service

```bash
# Start the service
sudo systemctl start nosvid.service

# Stop the service
sudo systemctl stop nosvid.service

# Restart the service
sudo systemctl restart nosvid.service

# Check service status
sudo systemctl status nosvid.service
```

### Enable/Disable Service at Boot

```bash
# Enable service to start at boot
sudo systemctl enable nosvid.service

# Disable service from starting at boot
sudo systemctl disable nosvid.service
```

## Viewing Logs

### View Service Logs

```bash
# View all logs with pagination
sudo journalctl -u nosvid.service

# View recent logs
sudo journalctl -u nosvid.service -n 100

# Follow logs in real-time
sudo journalctl -u nosvid.service -f

# View logs since a specific time
sudo journalctl -u nosvid.service --since "2023-01-01"
sudo journalctl -u nosvid.service --since "1 hour ago"
```

### View Application Logs

If the application writes to its own log files:

```bash
# View the main log file
tail -f ~/nosvid/logs/nosvid.log

# View error logs
tail -f ~/nosvid/logs/error.log
```

## Managing Scheduled Jobs

The application uses APScheduler for scheduled jobs:

```bash
# View scheduled jobs status
./nosvid status

# View scheduled jobs in the web interface
http://localhost:2121/status
```

## Updating YouTube Cookies

```bash
# Upload cookies from local browser to server
./upload_youtube_cookies.sh -b firefox -u kim -h videos.bitcoinops.de -p ~/nosvid -r
```

## Manual Commands

### Sync Videos

```bash
# Sync metadata for all videos
./nosvid sync

# Sync metadata with force refresh
./nosvid sync --force-refresh

# Sync metadata for a specific number of videos
./nosvid sync --max-videos 10
```

### Download Videos

```bash
# Download the oldest pending video
./nosvid download

# Download a specific video
./nosvid download VIDEO_ID

# Download all pending videos
./nosvid download --all-pending
```

### Upload to Nostrmedia

```bash
# Upload the oldest pending video to Nostrmedia
./nosvid nostrmedia

# Upload a specific video to Nostrmedia
./nosvid nostrmedia VIDEO_ID
```

### Post to Nostr

```bash
# Post the oldest pending video to Nostr
./nosvid nostr

# Post a specific video to Nostr
./nosvid nostr VIDEO_ID
```

### List Videos

```bash
# List all videos
./nosvid list

# List only downloaded videos
./nosvid list --downloaded

# List only videos that have not been downloaded
./nosvid list --not-downloaded
```

## Web Interface

```bash
# Start the web interface
./nosvid serve

# Access the web interface
http://localhost:2121
```

## Troubleshooting

### Check Configuration

```bash
# View current configuration
cat ~/nosvid/config.yaml
```

### Check Consistency

```bash
# Check for inconsistencies in metadata
./nosvid consistency-check

# Fix inconsistencies in metadata
./nosvid consistency-check --fix
```

### Check Disk Space

```bash
# Check disk space usage
df -h

# Check size of the repository
du -sh ~/nosvid/repository
```

### Check Network Connectivity

```bash
# Test connection to Nostr relays
ping wss://relay.damus.io

# Test connection to Nostrmedia
ping nostrmedia.com
```

## Backup and Restore

### Backup Configuration and Metadata

```bash
# Backup configuration
cp ~/nosvid/config.yaml ~/nosvid/config.yaml.bak

# Backup metadata
tar -czvf ~/nosvid_metadata_backup.tar.gz ~/nosvid/repository/*/metadata
```

### Restore from Backup

```bash
# Restore configuration
cp ~/nosvid/config.yaml.bak ~/nosvid/config.yaml

# Restore metadata
tar -xzvf ~/nosvid_metadata_backup.tar.gz -C /
```

#!/bin/bash

# This script installs NosVid, webhook handler, and updater as systemd services

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
NOSVID_DIR="$SCRIPT_DIR"

# Get the current user
CURRENT_USER=$(whoami)

# Get the path to the Python virtual environment
VENV_PATH="$NOSVID_DIR/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    "$VENV_PATH/bin/pip" install -e "$NOSVID_DIR"
    "$VENV_PATH/bin/pip" install requests browser_cookie3 p2pnetwork PyJWT
fi

# Check for required system dependencies
echo "Checking for required system dependencies..."

# Check for yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo "yt-dlp not found. Installing..."
    # Try to install yt-dlp using pip in the virtual environment
    "$VENV_PATH/bin/pip" install yt-dlp

    # Create a symlink to make yt-dlp available system-wide
    echo "Creating symlink for yt-dlp..."
    sudo ln -sf "$VENV_PATH/bin/yt-dlp" /usr/local/bin/yt-dlp
else
    echo "yt-dlp is already installed."
fi

# Create backup directory
mkdir -p "$NOSVID_DIR/backups"

# Create deployment directory
mkdir -p "$NOSVID_DIR/deployment"

# Ask for GitHub webhook secret
read -r -p "Enter GitHub webhook secret (leave empty to skip): " GITHUB_WEBHOOK_SECRET

# Create the NosVid service file
cat > "$NOSVID_DIR/deployment/nosvid.service" << EOF
[Unit]
Description=NosVid Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$NOSVID_DIR
ExecStart=$VENV_PATH/bin/python $NOSVID_DIR/nosvid serve
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$VENV_PATH/bin

[Install]
WantedBy=multi-user.target
EOF

# Create the webhook handler service file
cat > "$NOSVID_DIR/deployment/nosvid-webhook.service" << EOF
[Unit]
Description=NosVid GitHub Webhook Handler
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$NOSVID_DIR
ExecStart=$VENV_PATH/bin/python $NOSVID_DIR/webhook_handler.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=GITHUB_WEBHOOK_SECRET=$GITHUB_WEBHOOK_SECRET
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$VENV_PATH/bin

[Install]
WantedBy=multi-user.target
EOF

# Create the updater service file
cat > "$NOSVID_DIR/deployment/nosvid-updater.service" << EOF
[Unit]
Description=NosVid Updater Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$NOSVID_DIR
ExecStart=$VENV_PATH/bin/python $NOSVID_DIR/updater.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$VENV_PATH/bin

[Install]
WantedBy=multi-user.target
EOF

# Create the DecData service file
cat > "$NOSVID_DIR/deployment/decdata.service" << EOF
[Unit]
Description=DecData Service
After=network.target nosvid.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$NOSVID_DIR
ExecStart=$VENV_PATH/bin/python $NOSVID_DIR/decdata start --port 2122 --nosvid-api-url http://localhost:2121/api
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/usr/local/bin:/usr/bin:/bin:$VENV_PATH/bin

[Install]
WantedBy=multi-user.target
EOF

# Make the scripts executable
chmod +x "$NOSVID_DIR/nosvid"
chmod +x "$NOSVID_DIR/decdata"
chmod +x "$NOSVID_DIR/webhook_handler.py"
chmod +x "$NOSVID_DIR/updater.py"

# Copy the service files to the systemd directory
echo "Installing systemd services..."
sudo cp "$NOSVID_DIR/deployment/nosvid.service" /etc/systemd/system/
sudo cp "$NOSVID_DIR/deployment/nosvid-webhook.service" /etc/systemd/system/
sudo cp "$NOSVID_DIR/deployment/nosvid-updater.service" /etc/systemd/system/
sudo cp "$NOSVID_DIR/deployment/decdata.service" /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start the services
echo "Enabling services..."
sudo systemctl enable nosvid.service
sudo systemctl enable nosvid-webhook.service
sudo systemctl enable nosvid-updater.service
sudo systemctl enable decdata.service

echo "Starting services..."
sudo systemctl start nosvid.service
sudo systemctl start nosvid-webhook.service
sudo systemctl start nosvid-updater.service
sudo systemctl start decdata.service

echo "Services installed and started."
echo
echo "NosVid service:"
echo "  sudo systemctl status nosvid.service"
echo "  sudo journalctl -u nosvid.service -f"
echo
echo "Webhook handler service:"
echo "  sudo systemctl status nosvid-webhook.service"
echo "  sudo journalctl -u nosvid-webhook.service -f"
echo
echo "Updater service:"
echo "  sudo systemctl status nosvid-updater.service"
echo "  sudo journalctl -u nosvid-updater.service -f"
echo
echo "DecData service:"
echo "  sudo systemctl status decdata.service"
echo "  sudo journalctl -u decdata.service -f"
echo
echo "The DecData node is now running on port 2122."
echo "You can connect to it from other machines using:"
echo "  decdata connect --host $(hostname -I | awk '{print $1}') --port 2122"
echo
echo "GitHub webhook URL: http://your-server-ip:9000/webhook"
echo "Make sure to configure this URL in your GitHub repository settings."
echo "Settings > Webhooks > Add webhook"
echo "  Payload URL: http://your-server-ip:9000/webhook"
echo "  Content type: application/json"
echo "  Secret: $GITHUB_WEBHOOK_SECRET"
echo "  Events: Just the push event"
echo "  Active: Checked"

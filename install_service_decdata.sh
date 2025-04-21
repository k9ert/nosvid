#!/bin/bash

# This script installs DecData as a systemd service

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DECDATA_DIR="$SCRIPT_DIR"

# Get the current user
CURRENT_USER=$(whoami)

# Get the path to the Python virtual environment
VENV_PATH="$DECDATA_DIR/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH"
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    "$VENV_PATH/bin/pip" install -e "$DECDATA_DIR"
    "$VENV_PATH/bin/pip" install p2pnetwork requests
fi

# Check for required system dependencies
echo "Checking for required system dependencies..."

# Create the DecData service file
cat > /tmp/decdata.service << EOF
[Unit]
Description=DecData Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$DECDATA_DIR
ExecStart=$VENV_PATH/bin/python $DECDATA_DIR/run_node.py --port 2122
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
chmod +x "$DECDATA_DIR/run_node.py"
chmod +x "$DECDATA_DIR/connect_to_node.py"

# Copy the service file to the systemd directory
echo "Installing systemd service..."
sudo cp /tmp/decdata.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start the service
echo "Enabling service..."
sudo systemctl enable decdata.service

echo "Starting service..."
sudo systemctl start decdata.service

echo "Service installed and started."
echo
echo "DecData service:"
echo "  sudo systemctl status decdata.service"
echo "  sudo journalctl -u decdata.service -f"
echo
echo "The DecData node is now running on port 2122."
echo "You can connect to it from other machines using:"
echo "  python connect_to_node.py --host $(hostname -I | awk '{print $1}') --port 2122"
echo
echo "To configure NosVid integration, edit the service file:"
echo "  sudo systemctl stop decdata.service"
echo "  sudo nano /etc/systemd/system/decdata.service"
echo "  # Add --nosvid-repo or --nosvid-api-url parameters to ExecStart"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl start decdata.service"

#!/bin/bash

# This script refreshes the YouTube cookies file by exporting cookies from a browser

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
NOSVID_DIR="$SCRIPT_DIR"
VENV_PATH="$NOSVID_DIR/venv"

# Default cookies file path
DEFAULT_COOKIES_FILE="$NOSVID_DIR/www.youtube.com_cookies.txt"

# Parse command line arguments
BROWSER="chrome"
COOKIES_FILE="$DEFAULT_COOKIES_FILE"

# Display help message
function show_help {
    echo "Usage: $0 [options]"
    echo "Refresh YouTube cookies by exporting them from a browser"
    echo ""
    echo "Options:"
    echo "  -b, --browser BROWSER   Browser to export cookies from (chrome, firefox, safari, edge, opera)"
    echo "  -o, --output FILE       File to save cookies to (default: $DEFAULT_COOKIES_FILE)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --browser firefox --output my_cookies.txt"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -o|--output)
            COOKIES_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if the virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH"
    echo "Please run install_service.sh first"
    exit 1
fi

# Check if the export_cookies.py script exists
if [ ! -f "$NOSVID_DIR/export_cookies.py" ]; then
    echo "export_cookies.py script not found at $NOSVID_DIR/export_cookies.py"
    exit 1
fi

# Make the script executable
chmod +x "$NOSVID_DIR/export_cookies.py"

# Export cookies
echo "Exporting YouTube cookies from $BROWSER to $COOKIES_FILE..."
"$VENV_PATH/bin/python" "$NOSVID_DIR/export_cookies.py" --browser "$BROWSER" --domain "youtube.com" --output "$COOKIES_FILE"

# Check if the export was successful
if [ $? -ne 0 ]; then
    echo "Failed to export cookies"
    exit 1
fi

# Update the config.yaml file if it exists
CONFIG_FILE="$NOSVID_DIR/config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    echo "Updating config.yaml with the new cookies file path..."
    
    # Check if the youtube section exists
    if grep -q "youtube:" "$CONFIG_FILE"; then
        # Check if the cookies_file entry exists
        if grep -q "cookies_file:" "$CONFIG_FILE"; then
            # Update the cookies_file entry
            sed -i "s|cookies_file:.*|cookies_file: $COOKIES_FILE|" "$CONFIG_FILE"
        else
            # Add the cookies_file entry to the youtube section
            sed -i "/youtube:/a\\  cookies_file: $COOKIES_FILE" "$CONFIG_FILE"
        fi
    else
        # Add the youtube section with the cookies_file entry
        echo "" >> "$CONFIG_FILE"
        echo "youtube:" >> "$CONFIG_FILE"
        echo "  cookies_file: $COOKIES_FILE" >> "$CONFIG_FILE"
    fi
fi

echo "YouTube cookies refreshed successfully!"
echo "You may need to restart the NosVid service for the changes to take effect:"
echo "  sudo systemctl restart nosvid.service"

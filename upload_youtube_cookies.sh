#!/bin/bash

# This script exports YouTube cookies from a local browser and uploads them to a remote server

# Default values
BROWSER="chrome"
LOCAL_COOKIES_FILE="/tmp/www.youtube.com_cookies.txt"
REMOTE_USER=""
REMOTE_HOST=""
REMOTE_PATH=""
RESTART_SERVICE=false

# Display help message
function show_help {
    echo "Usage: $0 [options]"
    echo "Export YouTube cookies from a local browser and upload them to a remote server"
    echo ""
    echo "Options:"
    echo "  -b, --browser BROWSER   Browser to export cookies from (chrome, firefox, safari, edge, opera)"
    echo "  -l, --local FILE        Local file to save cookies to (default: $LOCAL_COOKIES_FILE)"
    echo "  -u, --user USER         Remote username"
    echo "  -h, --host HOST         Remote hostname or IP address"
    echo "  -p, --path PATH         Remote path to upload cookies to"
    echo "  -r, --restart           Restart the NosVid service on the remote server"
    echo "  --help                  Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 -b chrome -u kim -h videos.bitcoinops.de -p ~/nosvid -r"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -l|--local)
            LOCAL_COOKIES_FILE="$2"
            shift 2
            ;;
        -u|--user)
            REMOTE_USER="$2"
            shift 2
            ;;
        -h|--host)
            REMOTE_HOST="$2"
            shift 2
            ;;
        -p|--path)
            REMOTE_PATH="$2"
            shift 2
            ;;
        -r|--restart)
            RESTART_SERVICE=true
            shift
            ;;
        --help)
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

# Check required parameters
if [ -z "$REMOTE_USER" ] || [ -z "$REMOTE_HOST" ] || [ -z "$REMOTE_PATH" ]; then
    echo "Error: Remote user, host, and path are required"
    show_help
    exit 1
fi

# Check if browser_cookie3 is installed
if ! python3 -c "import browser_cookie3" &>/dev/null; then
    echo "Installing browser_cookie3..."
    pip3 install browser_cookie3
fi

# Create a temporary Python script to export cookies
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
#!/usr/bin/env python3
import sys
import browser_cookie3

def export_cookies(browser, domain, output_file):
    try:
        # Get cookies from browser
        if browser == 'chrome':
            cj = browser_cookie3.chrome(domain_name=domain)
        elif browser == 'firefox':
            cj = browser_cookie3.firefox(domain_name=domain)
        elif browser == 'safari':
            cj = browser_cookie3.safari(domain_name=domain)
        elif browser == 'edge':
            cj = browser_cookie3.edge(domain_name=domain)
        elif browser == 'opera':
            cj = browser_cookie3.opera(domain_name=domain)
        else:
            print(f"Unsupported browser: {browser}")
            return False
        
        # Save cookies to file
        with open(output_file, 'w') as f:
            for cookie in cj:
                f.write(f"{cookie.domain}\tTRUE\t{cookie.path}\t{cookie.secure}\t{cookie.expires}\t{cookie.name}\t{cookie.value}\n")
        
        # Count cookies
        cookie_count = len(cj)
        if cookie_count == 0:
            print(f"No cookies found for {domain} in {browser}")
            return False
        
        print(f"Exported {cookie_count} cookies for {domain} from {browser} to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error exporting cookies: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py BROWSER DOMAIN OUTPUT_FILE")
        sys.exit(1)
    
    browser = sys.argv[1]
    domain = sys.argv[2]
    output_file = sys.argv[3]
    
    success = export_cookies(browser, domain, output_file)
    sys.exit(0 if success else 1)
EOF

# Make the script executable
chmod +x "$TEMP_SCRIPT"

# Export cookies
echo "Exporting YouTube cookies from $BROWSER..."
python3 "$TEMP_SCRIPT" "$BROWSER" "youtube.com" "$LOCAL_COOKIES_FILE"

# Check if the export was successful
if [ $? -ne 0 ]; then
    echo "Failed to export cookies"
    rm "$TEMP_SCRIPT"
    exit 1
fi

# Upload cookies to the remote server
echo "Uploading cookies to $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH..."
scp "$LOCAL_COOKIES_FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"

# Check if the upload was successful
if [ $? -ne 0 ]; then
    echo "Failed to upload cookies"
    rm "$TEMP_SCRIPT"
    exit 1
fi

# Restart the NosVid service if requested
if [ "$RESTART_SERVICE" = true ]; then
    echo "Restarting NosVid service on $REMOTE_HOST..."
    ssh "$REMOTE_USER@$REMOTE_HOST" "sudo systemctl restart nosvid.service"
    
    # Check if the restart was successful
    if [ $? -ne 0 ]; then
        echo "Failed to restart NosVid service"
        rm "$TEMP_SCRIPT"
        exit 1
    fi
    
    echo "NosVid service restarted successfully"
fi

# Clean up
rm "$TEMP_SCRIPT"

echo "YouTube cookies uploaded successfully!"
echo ""
echo "If you need to update your config.yaml on the remote server, run:"
echo "ssh $REMOTE_USER@$REMOTE_HOST \"echo 'youtube:' >> ~/nosvid/config.yaml\""
echo "ssh $REMOTE_USER@$REMOTE_HOST \"echo '  cookies_file: $REMOTE_PATH/www.youtube.com_cookies.txt' >> ~/nosvid/config.yaml\""

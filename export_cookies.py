#!/usr/bin/env python3
"""
Export cookies from a browser to a file that can be used by yt-dlp.

This script uses the browser_cookie3 library to extract cookies from your browser
and save them in a format that yt-dlp can use.
"""

import os
import sys
import argparse
import browser_cookie3
import http.cookiejar
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("export_cookies")

def export_cookies(browser, domain, output_file):
    """
    Export cookies from a browser to a file.

    Args:
        browser: Browser to export cookies from ('chrome', 'firefox', 'safari', 'edge', 'opera')
        domain: Domain to export cookies for (e.g., 'youtube.com')
        output_file: File to save cookies to
    """
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
            logger.error(f"Unsupported browser: {browser}")
            return False

        # Save cookies to file
        with open(output_file, 'w') as f:
            for cookie in cj:
                f.write(f"{cookie.domain}\tTRUE\t{cookie.path}\t{cookie.secure}\t{cookie.expires}\t{cookie.name}\t{cookie.value}\n")

        # Count cookies
        cookie_count = len(cj)
        if cookie_count == 0:
            logger.warning(f"No cookies found for {domain} in {browser}")
            return False

        logger.info(f"Exported {cookie_count} cookies for {domain} from {browser} to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error exporting cookies: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Export cookies from a browser to a file')
    parser.add_argument('--browser', choices=['chrome', 'firefox', 'safari', 'edge', 'opera'],
                        default='chrome', help='Browser to export cookies from')
    parser.add_argument('--domain', default='youtube.com',
                        help='Domain to export cookies for (e.g., youtube.com)')
    parser.add_argument('--output', default='cookies.txt',
                        help='File to save cookies to')

    args = parser.parse_args()

    # Export cookies
    success = export_cookies(args.browser, args.domain, args.output)

    if success:
        print(f"Cookies exported successfully to {args.output}")
        print("You can use these cookies with yt-dlp by setting:")
        print(f"  YOUTUBE_COOKIES_FILE={os.path.abspath(args.output)}")
        print("Or by using the --cookies option:")
        print(f"  yt-dlp --cookies {os.path.abspath(args.output)} [URL]")
    else:
        print("Failed to export cookies")
        sys.exit(1)

if __name__ == "__main__":
    main()

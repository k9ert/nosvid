"""
Main entry point for nosvid
"""

import sys
from .cli.commands import main

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
DecData - Decentralized Video Data Exchange

Main entry point for the DecData package when run as a module.
"""

import sys
from importlib import import_module
from pathlib import Path

# Add the parent directory to sys.path to allow importing the decdata script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the main function from the decdata script
from decdata import main

if __name__ == "__main__":
    main()

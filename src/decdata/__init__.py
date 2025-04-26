"""
DecData - Decentralized Video Data Exchange

A peer-to-peer network application for distributing video content collected by the NosVid project.
"""

__version__ = '0.1.0'

# Import the main function from the decdata script to make it available
# when importing the package
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow importing the decdata script
script_path = Path(__file__).parent.parent.parent / 'decdata'
if script_path.exists():
    # Import main function from the decdata script
    sys.path.insert(0, str(script_path.parent))
    try:
        from decdata import main
        # Export the main function
        __all__ = ['main']
    except ImportError:
        def main():
            print("Error: Failed to import from decdata script")
            sys.exit(1)
else:
    # Fallback if the script is not found
    def main():
        print("Error: decdata script not found")
        sys.exit(1)

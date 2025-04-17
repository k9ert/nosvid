"""
Command-line interface commands for nosvid
"""

import sys
from .commands.main import main

if __name__ == '__main__':
    sys.exit(main())
else:
    # For backward compatibility
    from .commands.main import main as main_func
    main = main_func

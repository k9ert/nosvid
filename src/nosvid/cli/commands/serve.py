"""
Serve command for nosvid
"""

from ...web.app import run as run_web_app
from ...utils.config import get_default_web_port

def add_serve_command(subparsers):
    """
    Add the serve command to the subparsers

    Args:
        subparsers: Subparsers object
    """
    serve_parser = subparsers.add_parser(
        'serve',
        help='Run the web interface',
        description='Start a web server to manage videos through a browser interface'
    )
    serve_parser.add_argument(
        '--port',
        type=int,
        default=get_default_web_port(),
        help='Port to run the web server on (default: from config or 2121)'
    )
    serve_parser.set_defaults(func=serve_command)

def serve_command(args):
    """
    Run the web interface

    Args:
        args: Command line arguments

    Returns:
        int: Exit code
    """
    try:
        port = args.port
        print(f"Starting web interface on port {port}...")
        run_web_app(port=port)
        return 0
    except Exception as e:
        print(f"Error running web interface: {e}")
        return 1

"""
Serve command for nosvid
"""

from ...web.app import run as run_web_app

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
    serve_parser.set_defaults(func=serve_command)

def serve_command(_):
    """
    Run the web interface

    Args:
        _: Command line arguments (unused)

    Returns:
        int: Exit code
    """
    try:
        print("Starting web interface...")
        run_web_app()
        return 0
    except Exception as e:
        print(f"Error running web interface: {e}")
        return 1

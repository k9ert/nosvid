"""
Web interface for nosvid
"""

from .app import run


def run_web_app(port=2121, with_cronjobs=False):
    """
    Run the web application

    Args:
        port: Port to run the server on
        with_cronjobs: Whether to enable scheduled jobs (cronjobs)
    """
    run(port=port, with_cronjobs=with_cronjobs)

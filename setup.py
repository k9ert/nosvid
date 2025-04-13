#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="nosvid",
    version="0.1.0",
    description="A tool for downloading and managing YouTube videos",
    author="k9ert",
    author_email="",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "google-api-python-client",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "pyyaml",
        "yt-dlp>=2025.3.31",
    ],
    entry_points={
        "console_scripts": [
            "nosvid=nosvid.cli.commands:main",
        ],
    },
    python_requires=">=3.6",
)

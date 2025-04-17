#!/usr/bin/env python3
from setuptools import setup, find_packages

# Define dependencies
INSTALL_REQUIRES = [
    "google-api-python-client>=2.86.0",
    "google-auth>=2.22.0",
    "google-auth-oauthlib>=1.0.0",
    "google-auth-httplib2>=0.1.0",
    "pyyaml>=6.0.1",
    "yt-dlp>=2025.3.31",
    "requests>=2.25.0",
]

# Optional dependencies
EXTRAS_REQUIRE = {
    "nostrmedia": ["nostr-sdk>=0.41.0"],
    "dev": ["pytest", "black", "flake8"],
}

setup(
    name="nosvid",
    version="0.1.0",
    description="A tool for downloading and managing YouTube videos",
    author="k9ert",
    author_email="",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points={
        "console_scripts": [
            "nosvid=nosvid.cli.commands:main",
        ],
    },
    python_requires=">=3.6",
)

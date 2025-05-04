#!/usr/bin/env python3
from setuptools import find_packages, setup

# Define dependencies
INSTALL_REQUIRES = [
    # Core dependencies
    "google-api-python-client>=2.86.0",
    "google-auth>=2.22.0",
    "google-auth-oauthlib>=1.0.0",
    "google-auth-httplib2>=0.1.0",
    "pyyaml>=6.0.1",
    "yt-dlp>=2025.3.31",
    "requests>=2.25.0",
    "PyJWT>=2.6.0",  # Specifically PyJWT, not the 'jwt' package
    # Nostr dependencies
    "nostr-sdk>=0.41.0",
    # Web interface dependencies
    "fastapi>=0.95.0",
    "uvicorn>=0.21.1",
    "jinja2>=3.1.2",
    "pydantic>=1.10.7",
    "python-multipart>=0.0.6",
    "apscheduler>=3.10.1",
    # decdata
    "p2pnetwork>=1.2",
]

# Optional dependencies (only for development)
EXTRAS_REQUIRE = {
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "black>=23.3.0",
        "flake8>=6.0.0",
        "isort>=5.12.0",
        "mypy>=1.3.0",
        "pre-commit>=3.3.2",
    ],
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
            "decdata=decdata:main",
        ],
    },
    python_requires=">=3.6",
)

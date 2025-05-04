#!/bin/bash
# Setup development environment for NosVid

# Exit on error
set -e

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "Please run this script from the root of the repository"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install development dependencies
echo "Installing development dependencies..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

echo "Development environment setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To run the tests, run: ./nosvid test"
echo "Pre-commit hooks are now installed and will run automatically on commit"

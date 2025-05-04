"""
Test command for running pytest
"""

import os
import subprocess
import sys
from pathlib import Path


def register_test_parser(subparsers):
    """
    Register the test command parser

    Args:
        subparsers: Subparsers object from argparse
    """
    parser = subparsers.add_parser("test", help="Run tests")

    # Add arguments for the test command
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "test_path",
        nargs="?",
        default=None,
        help="Specific test path to run (e.g., tests/unit/decdata)",
    )


def test_command(args):
    """
    Run tests using pytest

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent.parent.parent

    # Build the pytest command
    pytest_args = ["pytest"]

    # Add markers based on arguments
    if args.unit and not args.integration:
        pytest_args.append("-m")
        pytest_args.append("unit")
    elif args.integration and not args.unit:
        pytest_args.append("-m")
        pytest_args.append("integration")

    # Add coverage if requested
    if args.coverage:
        pytest_args.append("--cov=src")
        pytest_args.append("--cov-report=term")
        pytest_args.append("--cov-report=html")

    # Add verbose output
    pytest_args.append("-v")

    # Add specific test path if provided
    if args.test_path:
        pytest_args.append(args.test_path)

    # Print the command being run
    print(f"Running: {' '.join(pytest_args)}")

    # Run pytest
    try:
        result = subprocess.run(pytest_args, cwd=str(project_root), check=False)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

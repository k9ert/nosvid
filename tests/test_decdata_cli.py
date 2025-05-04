#!/usr/bin/env python3
"""
Tests for the DecData CLI implementation.
"""

import unittest
from pathlib import Path


class TestDecDataCLI(unittest.TestCase):
    """Test cases for the DecData CLI."""

    def test_script_exists(self):
        """Test that the decdata script exists."""
        decdata_path = Path(__file__).parent.parent / "decdata"
        self.assertTrue(decdata_path.exists(), "decdata script not found")

    def test_serve_command_used(self):
        """Test that the serve command is used instead of start."""
        decdata_path = Path(__file__).parent.parent / "decdata"
        with open(decdata_path, "r") as f:
            content = f.read()

        # Check that the script uses 'serve' instead of 'start'
        self.assertIn("def serve_node(args):", content)
        self.assertNotIn("def start_node(args):", content)

        # Check that the command is 'serve' (with either single or double quotes)
        self.assertTrue(
            "serve_parser = subparsers.add_parser('serve'" in content
            or 'serve_parser = subparsers.add_parser("serve"' in content,
            "Could not find serve command parser",
        )
        self.assertFalse(
            "start_parser = subparsers.add_parser('start'" in content
            or 'start_parser = subparsers.add_parser("start"' in content,
            "Found deprecated start command parser",
        )

        # Check that the function is called correctly (with either single or double quotes)
        self.assertTrue(
            "if args.command == 'serve':" in content
            or 'if args.command == "serve":' in content,
            "Could not find serve command condition",
        )
        self.assertIn("serve_node(args)", content)


if __name__ == "__main__":
    unittest.main()

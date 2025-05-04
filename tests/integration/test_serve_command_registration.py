"""
Test that the serve command is registered correctly
"""

import subprocess
import unittest


class TestServeCommandRegistration(unittest.TestCase):
    """Test that the serve command is registered correctly"""

    def test_serve_command_registered(self):
        """Test that the serve command is registered in the parser"""
        # Run the help command to get the list of available commands
        result = subprocess.run(["./nosvid", "--help"], capture_output=True, text=True)

        # Check that the serve command is listed in the help output
        self.assertIn("serve", result.stdout)

    def test_serve_command_help(self):
        """Test that the serve command has help text"""
        # Run the help command for the serve command
        result = subprocess.run(
            ["./nosvid", "serve", "--help"], capture_output=True, text=True
        )

        # Check that the help text contains expected information
        self.assertIn("show this help message and exit", result.stdout)


if __name__ == "__main__":
    unittest.main()

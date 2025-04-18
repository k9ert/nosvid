"""
Simple integration test for the serve command
"""

import unittest
import subprocess

class TestServeSimple(unittest.TestCase):
    """Simple integration test for the serve command"""

    def test_serve_command_help(self):
        """Test that the serve command help works"""
        # Run the help command for the serve command
        result = subprocess.run(
            ["./nosvid", "serve", "--help"],
            capture_output=True,
            text=True
        )

        # Check that the help text contains expected information
        self.assertEqual(result.returncode, 0)
        self.assertIn("show this help message and exit", result.stdout)

if __name__ == "__main__":
    unittest.main()

"""
Integration test for the serve command
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

import requests


class TestServeCommand(unittest.TestCase):
    """Integration test for the serve command"""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment"""
        # Create a temporary directory for the test repository
        cls.temp_dir = tempfile.mkdtemp()

        # Create a test config file
        cls.config_file = os.path.join(cls.temp_dir, "config.yaml")
        with open(cls.config_file, "w") as f:
            f.write(
                """
defaults:
  output_dir: {}
channel:
  title: TestChannel
            """.format(
                    cls.temp_dir
                )
            )

        # Use a different port to avoid conflicts
        cls.port = 8124

        # Start the server using the serve command
        cls.server_process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                f"from src.nosvid.web.app import run; run(port={cls.port})",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "NOSVID_CONFIG": cls.config_file},
        )

        # Wait for the server to start
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment"""
        # Terminate the server process
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait()

        # Remove the temporary directory
        shutil.rmtree(cls.temp_dir)

    def test_homepage(self):
        """Test that the homepage loads correctly"""
        response = requests.get(f"http://localhost:{self.port}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("NosVid - Einundzwanzig Video Manager", response.text)

    def test_server_is_running(self):
        """Test that the server is running"""
        # Check if the process is still running
        self.assertIsNone(self.server_process.poll(), "Server process is not running")


if __name__ == "__main__":
    unittest.main()

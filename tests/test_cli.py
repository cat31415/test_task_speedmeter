import subprocess
import sys
import unittest
from pathlib import Path


class CliHelpTests(unittest.TestCase):
    def test_module_help_shows_available_options(self) -> None:
        project_root = Path(__file__).resolve().parents[1]

        completed = subprocess.run(
            [sys.executable, "-m", "speedmeter", "-h"],
            cwd=project_root,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertIn("usage: speedmeter", completed.stdout)
        self.assertIn("--requests", completed.stdout)
        self.assertIn("--timeout", completed.stdout)
        self.assertIn("--chunk-size", completed.stdout)


if __name__ == "__main__":
    unittest.main()

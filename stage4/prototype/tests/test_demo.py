"""Check the convenience runner without a model or network."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "run_demo.py"


class DemoRunnerTests(unittest.TestCase):
    def test_runner_keeps_expected_rejection_and_fresh_process_read(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "例 demo ! output"
            process = subprocess.run([sys.executable, "-B", str(RUNNER), "--output", str(output)], capture_output=True, encoding="utf-8")
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads((output / "demo-result.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "completed")
            self.assertEqual(len(result["examples"]), 4)
            self.assertEqual(result["steps"][4]["exit_code"], 2)
            self.assertFalse(result["stage3_completion_claimed"])
            self.assertEqual(result["provider_api_calls"], 0)
            writer = json.loads((output / "03-save.stdout.txt").read_text(encoding="utf-8"))
            reader = json.loads((output / "04-restart-read.stdout.txt").read_text(encoding="utf-8"))
            self.assertNotEqual(writer["pid"], reader["pid"])
            self.assertEqual(reader["state_sha256"], writer["state_sha256_after"])
            self.assertTrue((output / "summary.txt").is_file())

    def test_existing_output_is_not_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            marker = output / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            process = subprocess.run([sys.executable, "-B", str(RUNNER), "--output", str(output)], capture_output=True, encoding="utf-8")
            self.assertEqual(process.returncode, 1)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            self.assertEqual(list(output.iterdir()), [marker])


if __name__ == "__main__":
    unittest.main()

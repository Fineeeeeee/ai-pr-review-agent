import json
import tempfile
import unittest
from pathlib import Path

from ai_pr_review_agent.cli import run_cli


class CliTests(unittest.TestCase):
    def test_run_cli_reads_diff_file_and_returns_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            diff_path = Path(temp_dir) / "change.diff"
            diff_path.write_text(
                "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n",
                encoding="utf-8",
            )

            exit_code, output = run_cli(["--diff-file", str(diff_path), "--format", "json"])

        payload = json.loads(output)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["risk_level"], "critical")

    def test_run_cli_can_return_sarif(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            diff_path = Path(temp_dir) / "change.diff"
            diff_path.write_text(
                "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n",
                encoding="utf-8",
            )

            exit_code, output = run_cli(["--diff-file", str(diff_path), "--format", "sarif"])

        payload = json.loads(output)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["runs"][0]["results"][0]["ruleId"], "unsafe_eval")

    def test_run_cli_can_return_harness_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            diff_path = Path(temp_dir) / "change.diff"
            diff_path.write_text(
                "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n",
                encoding="utf-8",
            )

            exit_code, output = run_cli(["--diff-file", str(diff_path), "--format", "harness"])

        payload = json.loads(output)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["agent_harness"]["sandbox"]["mode"], "read_only_default")

    def test_run_cli_returns_error_for_missing_input(self):
        exit_code, output = run_cli([])

        self.assertEqual(exit_code, 2)
        self.assertIn("Provide --diff-file, --diff-text, or --repo", output)

    def test_run_cli_returns_error_for_invalid_format(self):
        exit_code, output = run_cli(["--diff-text", "diff --git a/app.py b/app.py", "--format", "xml"])

        self.assertEqual(exit_code, 2)
        self.assertIn("invalid choice", output)
        self.assertIn("xml", output)

    def test_run_cli_requires_env_key_when_deepseek_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            diff_path = Path(temp_dir) / "change.diff"
            diff_path.write_text(
                "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n",
                encoding="utf-8",
            )

            exit_code, output = run_cli(["--diff-file", str(diff_path), "--deepseek"])

        self.assertEqual(exit_code, 2)
        self.assertIn("DEEPSEEK_API_KEY", output)

    def test_run_cli_can_save_review_memory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            diff_path = temp_path / "change.diff"
            memory_path = temp_path / "memory.jsonl"
            diff_path.write_text(
                "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n",
                encoding="utf-8",
            )

            exit_code, _ = run_cli(
                [
                    "--diff-file",
                    str(diff_path),
                    "--save-memory",
                    str(memory_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(memory_path.exists())


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from ai_pr_review_agent.cli import run_cli
from ai_pr_review_agent.review_policy import parse_simple_yaml


class ReviewPolicyTests(unittest.TestCase):
    def test_parse_simple_yaml_supports_scalars_and_lists(self):
        config = parse_simple_yaml(
            """
fail_on: high
ignore_rules:
  - missing_tests
ignore_paths: ["docs/**", "*.md"]
"""
        )

        self.assertEqual(config["fail_on"], "high")
        self.assertEqual(config["ignore_rules"], ["missing_tests"])
        self.assertEqual(config["ignore_paths"], ["docs/**", "*.md"])

    def test_parse_simple_yaml_supports_custom_rule_entries(self):
        config = parse_simple_yaml(
            """
custom_rules:
  - id: team_no_pickle_loads
    pattern: "pickle.loads"
    severity: high
    message: "Team policy forbids unsafe pickle deserialization."
"""
        )

        self.assertEqual(
            config["custom_rules"],
            [
                {
                    "id": "team_no_pickle_loads",
                    "pattern": "pickle.loads",
                    "severity": "high",
                    "message": "Team policy forbids unsafe pickle deserialization.",
                }
            ],
        )

    def test_cli_applies_ignore_rules_before_risk_scoring(self):
        diff = "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+def f():\n+    return 1\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / ".ai-pr-review.yml"
            config_path.write_text("ignore_rules:\n  - missing_tests\n", encoding="utf-8")

            exit_code, output = run_cli(
                [
                    "--diff-text",
                    diff,
                    "--config",
                    str(config_path),
                    "--format",
                    "json",
                ]
            )

        payload = json.loads(output)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["risk_level"], "low")
        self.assertEqual(payload["findings"], [])

    def test_cli_applies_ignore_paths_before_risk_scoring(self):
        diff = "diff --git a/docs/example.py b/docs/example.py\n--- a/docs/example.py\n+++ b/docs/example.py\n@@ -1 +1,2 @@\n+eval(user_input)\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / ".ai-pr-review.yml"
            config_path.write_text("ignore_paths:\n  - docs/**\n", encoding="utf-8")

            exit_code, output = run_cli(
                [
                    "--diff-text",
                    diff,
                    "--config",
                    str(config_path),
                    "--format",
                    "json",
                ]
            )

        payload = json.loads(output)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["risk_level"], "low")
        self.assertEqual(payload["findings"], [])

    def test_cli_returns_nonzero_when_risk_gate_threshold_is_met(self):
        diff = "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n"

        exit_code, output = run_cli(["--diff-text", diff, "--fail-on-risk", "high"])

        self.assertEqual(exit_code, 3)
        self.assertIn("critical", output)

    def test_cli_uses_configured_fail_on_only_when_policy_is_enforced(self):
        diff = "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / ".ai-pr-review.yml"
            config_path.write_text("fail_on: high\n", encoding="utf-8")

            normal_exit_code, _ = run_cli(["--diff-text", diff, "--config", str(config_path)])
            enforced_exit_code, _ = run_cli(
                ["--diff-text", diff, "--config", str(config_path), "--enforce-policy"]
            )

        self.assertEqual(normal_exit_code, 0)
        self.assertEqual(enforced_exit_code, 3)

    def test_cli_applies_team_custom_rules_from_policy_config(self):
        diff = "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+value = pickle.loads(payload)\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / ".ai-pr-review.yml"
            config_path.write_text(
                """
custom_rules:
  - id: team_no_pickle_loads
    pattern: "pickle.loads"
    severity: high
    message: "Team policy forbids unsafe pickle deserialization."
""",
                encoding="utf-8",
            )

            exit_code, output = run_cli(
                [
                    "--diff-text",
                    diff,
                    "--config",
                    str(config_path),
                    "--format",
                    "json",
                ]
            )

        payload = json.loads(output)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["risk_level"], "high")
        self.assertEqual(payload["findings"][0]["rule_id"], "team_no_pickle_loads")
        self.assertIn("pickle deserialization", payload["findings"][0]["message"])


if __name__ == "__main__":
    unittest.main()

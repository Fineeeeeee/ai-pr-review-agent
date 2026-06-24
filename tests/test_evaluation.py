import json
import tempfile
import unittest
from pathlib import Path

from ai_pr_review_agent.evaluation import evaluate_dataset, render_evaluation_markdown


class EvaluationTests(unittest.TestCase):
    def test_evaluate_dataset_reports_recall_false_positives_and_latency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "case-secret.diff").write_text(
                "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+api_key = \"demo-api-key-value\"\n",
                encoding="utf-8",
            )
            (root / "case-doc.diff").write_text(
                "diff --git a/README.md b/README.md\n--- a/README.md\n+++ b/README.md\n@@ -1 +1,2 @@\n+docs update\n",
                encoding="utf-8",
            )
            (root / "manifest.json").write_text(
                json.dumps(
                    [
                        {
                            "id": "case-secret",
                            "file": "case-secret.diff",
                            "expected_rules": ["secret_literal", "missing_tests"],
                        },
                        {
                            "id": "case-doc",
                            "file": "case-doc.diff",
                            "expected_rules": [],
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = evaluate_dataset(root)

        self.assertEqual(result.sample_count, 2)
        self.assertEqual(result.expected_positive_count, 2)
        self.assertEqual(result.detected_positive_count, 2)
        self.assertEqual(result.false_positive_count, 0)
        self.assertEqual(result.recall_percent, 100.0)
        self.assertGreaterEqual(result.average_latency_ms, 0)

    def test_render_evaluation_markdown_contains_resume_ready_numbers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "case.diff").write_text(
                "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n",
                encoding="utf-8",
            )
            (root / "manifest.json").write_text(
                json.dumps(
                    [{"id": "case", "file": "case.diff", "expected_rules": ["unsafe_eval", "missing_tests"]}],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = evaluate_dataset(root)
            markdown = render_evaluation_markdown(result)

        self.assertIn("Sample Count", markdown)
        self.assertIn("Recall", markdown)
        self.assertIn("Average Latency", markdown)


if __name__ == "__main__":
    unittest.main()

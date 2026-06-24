import json
import unittest

from ai_pr_review_agent.deepseek_client import (
    build_deepseek_payload,
    build_deepseek_review_context,
    extract_deepseek_content,
)
from ai_pr_review_agent.reviewer import review_diff


class DeepSeekClientTests(unittest.TestCase):
    def test_build_deepseek_payload_uses_current_default_model(self):
        report = review_diff(
            "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n"
        )

        payload = build_deepseek_payload(report, "diff text")

        self.assertEqual(payload["model"], "deepseek-v4-flash")
        self.assertEqual(payload["stream"], False)
        self.assertIn("messages", payload)
        self.assertIn("中英文", payload["messages"][0]["content"])

    def test_build_deepseek_review_context_uses_context_strategy(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
+eval(user_input)
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
+docs update
"""
        report = review_diff(diff)

        context = build_deepseek_review_context(report, diff)

        self.assertIn("Context compression plan", context)
        self.assertIn("app.py -> full", context)
        self.assertIn("README.md -> skip", context)
        self.assertIn("eval(user_input)", context)

    def test_extract_deepseek_content_reads_openai_compatible_response(self):
        raw = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": "增强审查建议\nEnhanced review suggestion"
                        }
                    }
                ]
            }
        ).encode("utf-8")

        self.assertEqual(
            extract_deepseek_content(raw),
            "增强审查建议\nEnhanced review suggestion",
        )


if __name__ == "__main__":
    unittest.main()

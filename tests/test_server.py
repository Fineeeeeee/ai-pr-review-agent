import json
import unittest

from ai_pr_review_agent.server import build_home_page, review_payload


class ServerTests(unittest.TestCase):
    def test_build_home_page_contains_review_form(self):
        html = build_home_page()

        self.assertIn("AI PR Review Agent", html)
        self.assertIn("textarea", html)
        self.assertIn("/api/review", html)
        self.assertIn("riskBadge", html)
        self.assertIn("jsonView", html)

    def test_review_payload_returns_json_report(self):
        body = json.dumps(
            {
                "diff": "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n"
            }
        ).encode("utf-8")

        status, payload = review_payload(body)

        self.assertEqual(status, 200)
        self.assertEqual(payload["risk_level"], "critical")


if __name__ == "__main__":
    unittest.main()

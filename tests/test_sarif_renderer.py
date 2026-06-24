import json
import unittest

from ai_pr_review_agent.reviewer import review_diff
from ai_pr_review_agent.sarif_renderer import render_sarif


class SarifRendererTests(unittest.TestCase):
    def test_render_sarif_outputs_github_code_scanning_shape(self):
        report = review_diff(
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1,2 @@\n"
            "+eval(user_input)\n"
        )

        payload = json.loads(render_sarif(report))

        self.assertEqual(payload["version"], "2.1.0")
        self.assertEqual(payload["runs"][0]["tool"]["driver"]["name"], "AI PR Review Agent")
        self.assertEqual(payload["runs"][0]["results"][0]["ruleId"], "unsafe_eval")
        self.assertEqual(
            payload["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"],
            "app.py",
        )


if __name__ == "__main__":
    unittest.main()

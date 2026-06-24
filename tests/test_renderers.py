import json
import unittest

from ai_pr_review_agent.reviewer import review_diff
from ai_pr_review_agent.renderers import render_json, render_markdown


class RendererTests(unittest.TestCase):
    def test_render_json_contains_stable_schema(self):
        report = review_diff("diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n")

        payload = json.loads(render_json(report))

        self.assertEqual(payload["risk_level"], "critical")
        self.assertEqual(payload["findings"][0]["rule_id"], "unsafe_eval")

    def test_render_markdown_contains_resume_friendly_sections(self):
        report = review_diff("diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1,2 @@\n+eval(user_input)\n")

        markdown = render_markdown(report)

        self.assertIn("# AI Code Review Report / 智能代码审查报告", markdown)
        self.assertIn("Risk Level / 风险等级", markdown)
        self.assertIn("Recommended Test Plan", markdown)
        self.assertIn("为什么重要", markdown)
        self.assertIn("建议", markdown)
        self.assertIn("Agent Harness / Agent 运行框架", markdown)
        self.assertIn("Sandbox / 沙盒策略", markdown)


if __name__ == "__main__":
    unittest.main()

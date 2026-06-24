import tempfile
import unittest
from pathlib import Path

from ai_pr_review_agent.context_compressor import build_context_plan
from ai_pr_review_agent.impact_analysis import analyze_impact
from ai_pr_review_agent.review_memory import append_review_events, load_review_events
from ai_pr_review_agent.reviewer import review_diff


class AdvancedAnalysisTests(unittest.TestCase):
    def test_context_plan_prioritizes_security_files_and_skips_docs(self):
        diff = """diff --git a/auth/service.py b/auth/service.py
--- a/auth/service.py
+++ b/auth/service.py
@@ -1,2 +1,4 @@
+def login(user):
+    return eval(user)
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
+docs update
"""

        report = review_diff(diff)

        self.assertEqual(report.context_plan.total_files, 2)
        self.assertEqual(report.context_plan.file_strategies[0].strategy, "full")
        self.assertEqual(report.context_plan.file_strategies[0].reason, "high_risk_finding")
        self.assertEqual(report.context_plan.file_strategies[1].strategy, "skip")

    def test_impact_analysis_finds_direct_callers_for_changed_function(self):
        diff = """diff --git a/risk_engine.py b/risk_engine.py
--- a/risk_engine.py
+++ b/risk_engine.py
@@ -1,2 +1,3 @@
+def calculate_risk(order):
+    return "high"
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "order_service.py").write_text(
                "from risk_engine import calculate_risk\nscore = calculate_risk(order)\n",
                encoding="utf-8",
            )
            (root / "report_gen.py").write_text(
                "import risk_engine\nvalue = risk_engine.calculate_risk(order)\n",
                encoding="utf-8",
            )

            result = analyze_impact(diff, repo_path=root)

        self.assertEqual(result.impact_level, "medium")
        self.assertEqual(result.changed_symbols, ["calculate_risk"])
        self.assertEqual(
            sorted(call.file_path for call in result.direct_callers),
            ["order_service.py", "report_gen.py"],
        )

    def test_impact_analysis_extracts_async_and_class_methods(self):
        diff = """diff --git a/risk_engine.py b/risk_engine.py
--- a/risk_engine.py
+++ b/risk_engine.py
@@ -1,5 +1,7 @@
 class RiskEngine:
+    async def calculate_risk(self, order):
+        return "high"
+def normalize_score(score):
+    return score
"""

        result = analyze_impact(diff)

        self.assertEqual(result.changed_symbols, ["calculate_risk", "normalize_score"])

    def test_impact_analysis_extracts_function_from_hunk_context(self):
        diff = """diff --git a/risk_engine.py b/risk_engine.py
--- a/risk_engine.py
+++ b/risk_engine.py
@@ -10,7 +10,8 @@ def calculate_risk(order):
     score = 0
+    score += order.amount
     return score
"""

        result = analyze_impact(diff)

        self.assertEqual(result.changed_symbols, ["calculate_risk"])

    def test_structured_output_contains_ci_ready_fields(self):
        diff = """diff --git a/user_service.py b/user_service.py
--- a/user_service.py
+++ b/user_service.py
@@ -1,2 +1,3 @@
+cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
"""

        report = review_diff(diff)
        payload = report.to_dict()

        self.assertIn("structured_output", payload)
        self.assertEqual(payload["structured_output"]["risk_level"], "high")
        self.assertFalse(payload["structured_output"]["auto_approve_eligible"])
        self.assertIn("user_service.py", payload["structured_output"]["affected_files"])
        self.assertEqual(payload["structured_output"]["review_comments"][0]["rule_id"], "sql_interpolation")

    def test_review_memory_persists_events_as_jsonl(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
+eval(user_input)
"""
        report = review_diff(diff)
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "review-memory.jsonl"

            written = append_review_events(report, memory_path)
            loaded = load_review_events(memory_path)

        self.assertEqual(written, 2)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["feedback_status"], "pending")
        self.assertIn(loaded[0]["rule_id"], {"unsafe_eval", "missing_tests"})


class ContextPlanUnitTests(unittest.TestCase):
    def test_build_context_plan_summarizes_modules_and_line_counts(self):
        diff = """diff --git a/payment/risk.py b/payment/risk.py
--- a/payment/risk.py
+++ b/payment/risk.py
@@ -1 +1,4 @@
+def calculate_risk(order):
+    return "high"
+# changed
diff --git a/tests/test_risk.py b/tests/test_risk.py
--- a/tests/test_risk.py
+++ b/tests/test_risk.py
@@ -1 +1,2 @@
+def test_risk():
+    assert True
"""
        report = review_diff(diff)
        plan = build_context_plan(report.summary, report.findings)

        self.assertEqual(plan.total_files, 2)
        self.assertEqual(plan.total_added_lines, 5)
        self.assertIn("payment", plan.modules)
        self.assertIn("tests", plan.modules)
        self.assertEqual(
            {item.file_path: item.added_lines for item in plan.file_strategies},
            {"payment/risk.py": 3, "tests/test_risk.py": 2},
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from ai_pr_review_agent.reviewer import review_diff


class ReviewerTests(unittest.TestCase):
    def test_review_diff_flags_secret_and_sql_interpolation(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
+api_key = "demo-api-key-value"
+cursor.execute(f"select * from users where id = {user_id}")
"""

        report = review_diff(diff)

        rule_ids = {finding.rule_id for finding in report.findings}
        self.assertIn("secret_literal", rule_ids)
        self.assertIn("sql_interpolation", rule_ids)
        self.assertEqual(report.risk_level, "high")
        self.assertEqual(report.findings[0].title_zh, "疑似密钥被提交到代码中")

    def test_review_diff_flags_sql_interpolation_through_query_variable(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
+query = f"select * from users where id = {user_id}"
+cursor.execute(query)
"""

        report = review_diff(diff)

        sql_findings = [finding for finding in report.findings if finding.rule_id == "sql_interpolation"]
        self.assertEqual(len(sql_findings), 1)
        self.assertEqual(sql_findings[0].line_number, 2)

    def test_review_diff_flags_sql_format_assignment_through_ast(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
+query = "select * from users where id = {}".format(user_id)
+cursor.execute(query)
"""

        report = review_diff(diff)

        sql_findings = [finding for finding in report.findings if finding.rule_id == "sql_interpolation"]
        self.assertEqual(len(sql_findings), 1)
        self.assertEqual(sql_findings[0].line_number, 2)

    def test_review_diff_flags_sql_percent_assignment_through_ast(self):
        diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,2 +1,4 @@
+query = "select * from users where id = %s" % user_id
+cursor.execute(query)
"""

        report = review_diff(diff)

        sql_findings = [finding for finding in report.findings if finding.rule_id == "sql_interpolation"]
        self.assertEqual(len(sql_findings), 1)
        self.assertEqual(sql_findings[0].line_number, 2)

    def test_review_diff_flags_javascript_template_sql_interpolation(self):
        diff = """diff --git a/app.js b/app.js
--- a/app.js
+++ b/app.js
@@ -1,2 +1,4 @@
+const query = `select * from users where id = ${userId}`;
+db.query(query);
"""

        report = review_diff(diff)

        rule_ids = {finding.rule_id for finding in report.findings}
        self.assertIn("sql_interpolation", rule_ids)
        self.assertIn("missing_tests", rule_ids)

    def test_review_diff_flags_typescript_sql_string_concat(self):
        diff = """diff --git a/service.ts b/service.ts
--- a/service.ts
+++ b/service.ts
@@ -1,2 +1,4 @@
+const query = "select * from users where id = " + userId;
+connection.execute(query);
"""

        report = review_diff(diff)

        rule_ids = {finding.rule_id for finding in report.findings}
        self.assertIn("sql_interpolation", rule_ids)

    def test_review_diff_flags_javascript_secret_eval_and_shell_exec(self):
        diff = """diff --git a/app.js b/app.js
--- a/app.js
+++ b/app.js
@@ -1,2 +1,5 @@
+const apiKey = "demo-api-key-value";
+eval(userInput);
+child_process.exec(command);
"""

        report = review_diff(diff)

        rule_ids = {finding.rule_id for finding in report.findings}
        self.assertIn("secret_literal", rule_ids)
        self.assertIn("unsafe_eval", rule_ids)
        self.assertIn("shell_execution", rule_ids)

    def test_review_diff_marks_missing_tests_for_application_changes(self):
        diff = """diff --git a/service.py b/service.py
--- a/service.py
+++ b/service.py
@@ -1,2 +1,3 @@
+def calculate_total(items):
+    return sum(items)
"""

        report = review_diff(diff)

        self.assertIn("missing_tests", {finding.rule_id for finding in report.findings})
        self.assertIn("service.py", report.summary.changed_files)
        self.assertIn("为变更行为补充聚焦测试", report.test_plan_zh[-1])

    def test_review_diff_accepts_test_only_changes_as_low_risk(self):
        diff = """diff --git a/tests/test_service.py b/tests/test_service.py
--- a/tests/test_service.py
+++ b/tests/test_service.py
@@ -1,2 +1,3 @@
+def test_total():
+    assert True
"""

        report = review_diff(diff)

        self.assertEqual(report.risk_level, "low")
        self.assertEqual(report.findings, [])


if __name__ == "__main__":
    unittest.main()

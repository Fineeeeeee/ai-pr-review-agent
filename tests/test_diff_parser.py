import unittest

from ai_pr_review_agent.diff_parser import parse_unified_diff


SAMPLE_DIFF = """diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,5 @@
 import sqlite3
+password = "demo-password-value"
+cursor.execute(f"select * from users where id = {user_id}")
 print("done")
diff --git a/tests/test_app.py b/tests/test_app.py
new file mode 100644
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1,2 @@
+def test_smoke():
+    assert True
"""


class DiffParserTests(unittest.TestCase):
    def test_parse_unified_diff_groups_files_and_added_lines(self):
        result = parse_unified_diff(SAMPLE_DIFF)

        self.assertEqual([file.path for file in result.files], ["app.py", "tests/test_app.py"])
        self.assertEqual(result.files[0].added_lines[0].content, 'password = "demo-password-value"')
        self.assertEqual(result.files[0].added_lines[0].new_line_number, 2)
        self.assertTrue(result.has_tests)

    def test_parse_unified_diff_handles_empty_input(self):
        result = parse_unified_diff("")

        self.assertEqual(result.files, [])
        self.assertFalse(result.has_tests)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from ai_pr_review_agent.memory_cli import run_memory_cli
from ai_pr_review_agent.review_memory import load_review_events


class MemoryCliTests(unittest.TestCase):
    def test_run_memory_cli_marks_matching_event(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.jsonl"
            memory_path.write_text(
                '{"rule_id":"unsafe_eval","file":"app.py","line":2,"severity":"critical","feedback_status":"pending","developer_action":"unknown"}\n',
                encoding="utf-8",
            )

            exit_code, output = run_memory_cli(
                [
                    "--memory-file",
                    str(memory_path),
                    "--file",
                    "app.py",
                    "--line",
                    "2",
                    "--status",
                    "false_positive",
                ]
            )

            events = load_review_events(memory_path)

        self.assertEqual(exit_code, 0)
        self.assertIn("updated=1", output)
        self.assertEqual(events[0]["feedback_status"], "false_positive")
        self.assertEqual(events[0]["developer_action"], "reviewed")


if __name__ == "__main__":
    unittest.main()

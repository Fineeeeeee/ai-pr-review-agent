import json
import unittest

from ai_pr_review_agent.agent_harness import build_agent_harness
from ai_pr_review_agent.harness_renderer import render_harness_manifest
from ai_pr_review_agent.reviewer import review_diff


class AgentHarnessTests(unittest.TestCase):
    def test_build_agent_harness_contains_operational_layers(self):
        report = review_diff(
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1,2 @@\n"
            "+eval(user_input)\n"
        )

        harness = build_agent_harness(report)

        self.assertEqual(
            [agent.name for agent in harness.agents],
            ["diff_parser_agent", "rule_review_agent", "impact_agent", "context_agent", "llm_review_agent"],
        )
        self.assertEqual(
            [layer.name for layer in harness.memory_layers],
            ["working_memory", "review_memory", "pattern_memory"],
        )
        self.assertEqual(harness.sandbox.mode, "read_only_default")
        self.assertEqual(harness.resilience.fallbacks[0], "local_rule_engine")
        self.assertTrue(harness.observability.trace_id.startswith("review-"))

    def test_render_harness_manifest_outputs_machine_readable_json(self):
        report = review_diff(
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1 +1,2 @@\n"
            "+eval(user_input)\n"
        )

        payload = json.loads(render_harness_manifest(report))

        self.assertIn("agent_harness", payload)
        self.assertEqual(payload["agent_harness"]["sandbox"]["mode"], "read_only_default")
        self.assertIn("observability", payload["agent_harness"])
        self.assertEqual(payload["report"]["risk_level"], "critical")


if __name__ == "__main__":
    unittest.main()

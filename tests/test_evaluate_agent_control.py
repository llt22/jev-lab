import unittest

from scripts.evaluate_agent_control import (
    binary_metrics,
    lexical_path,
    recent_baseline,
    route_baseline,
    route_metrics,
)


class AgentControlMetricTests(unittest.TestCase):
    def test_binary_metrics(self):
        metrics = binary_metrics([True, True, False, False], [True, False, True, False])
        self.assertEqual(metrics["accuracy"], 0.5)
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 0.5)

    def test_recent_baseline_uses_lowest_age(self):
        cases = [{"id": "c", "artifacts": [{"id": "old", "age": 8}, {"id": "new", "age": 1}]}]
        self.assertEqual(recent_baseline(cases, 1), {"c": {"old": False, "new": True}})

    def test_lexical_path_prefers_overlap(self):
        selected = lexical_path("invoice pdf renderer", ["billing/payment.py", "billing/invoice_pdf_renderer.py"])
        self.assertEqual(selected, "billing/invoice_pdf_renderer.py")

    def test_route_baseline(self):
        self.assertEqual(route_baseline("Rename a local variable."), "small_local")
        self.assertEqual(route_baseline("Diagnose a distributed deadlock."), "strong_reasoning")
        self.assertEqual(route_baseline("Add an endpoint following existing patterns."), "fast_general")

    def test_route_metrics_penalizes_under_routing(self):
        cases = [{"id": "a", "route": "strong_reasoning"}, {"id": "b", "route": "small_local"}]
        metrics = route_metrics(cases, {"a": "fast_general", "b": "small_local"})
        self.assertEqual(metrics["accuracy"], 0.5)
        self.assertEqual(metrics["under_route_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()

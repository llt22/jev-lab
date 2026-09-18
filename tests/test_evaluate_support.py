import unittest

from scripts.evaluate_support import (
    calculate_metrics,
    expected_calibration_error,
    macro_f1,
    percentile,
    validate_response,
)
from scripts.evaluate_keyword_baseline import (
    classify_category,
    classify_missing_info,
    classify_urgent,
)


CATEGORIES = ["network", "account", "billing", "security", "product", "other"]


def result(case_id, group, expected_category, predicted_category, probability=0.8):
    probabilities = {category: 0.0 for category in CATEGORIES}
    probabilities[predicted_category] = probability
    remainder = (1.0 - probability) / (len(CATEGORIES) - 1)
    for category in CATEGORIES:
        if category != predicted_category:
            probabilities[category] = remainder
    return {
        "id": case_id,
        "group": group,
        "expected": {
            "category": expected_category,
            "urgent": True,
            "needs_human": False,
            "missing_info": False,
            "frustration": 1,
        },
        "latency_ms": 100.0,
        "response": {
            "model": "jev-test",
            "answers": {
                "category": {
                    "type": "choice",
                    "choice": predicted_category,
                    "probabilities": probabilities,
                    "confidence": 0.7,
                },
                "urgent": {"type": "noul", "noul": 0.9},
                "needs_human": {"type": "noul", "noul": 0.1},
                "missing_info": {"type": "noul", "noul": 0.1},
                "frustration": {
                    "type": "score",
                    "score": 1.0,
                    "confidence": 1.0,
                    "probabilities": {"0": 0.0, "1": 1.0, "2": 0.0},
                },
            },
            "usage": {"input_tokens": 100, "output_tokens": 20},
        },
    }


class MetricTests(unittest.TestCase):
    def test_percentile_interpolates(self):
        self.assertEqual(percentile([10, 20, 30], 0.5), 20)
        self.assertEqual(percentile([10, 20], 0.5), 15)

    def test_macro_f1_perfect(self):
        self.assertEqual(macro_f1(["a", "b"], ["a", "b"], ["a", "b"]), 1.0)

    def test_ece_perfect(self):
        self.assertAlmostEqual(expected_calibration_error([1.0, 1.0], [True, True]), 0.0)

    def test_calculate_metrics(self):
        metrics = calculate_metrics(
            [
                result("a", "g1", "network", "network"),
                result("b", "g1", "network", "network"),
                result("c", "g2", "billing", "account"),
            ],
            CATEGORIES,
        )
        self.assertEqual(metrics["completed"], 3)
        self.assertAlmostEqual(metrics["category"]["accuracy"], 2 / 3)
        self.assertEqual(metrics["usage"]["input_tokens"], 300)
        self.assertEqual(metrics["latency_ms"]["p50"], 100)

    def test_validate_response_rejects_missing_answer(self):
        with self.assertRaises(ValueError):
            validate_response({"answers": {}}, ["category"])

    def test_keyword_baseline_routes_security_before_account(self):
        self.assertEqual(classify_category("An attacker changed my account login"), "security")

    def test_keyword_baseline_respects_urgency_negation(self):
        self.assertFalse(classify_urgent("This is not urgent and can wait until tomorrow"))

    def test_keyword_baseline_detects_vague_input(self):
        self.assertTrue(classify_missing_info("It is broken. Fix it."))


if __name__ == "__main__":
    unittest.main()

import unittest

from scripts.evaluate_confidence_escalation import (
    answer_signals,
    build_questions,
    closest_level,
    decomposition_summary,
    gate_sweep,
    paired_context_rot,
)
from scripts.compare_confidence_runs import per_item, pooled_gates


def noul_response(probability):
    return {"answers": {"answer": {"type": "noul", "noul": probability}}}


def choice_response(choice, probabilities, confidence=None):
    return {
        "answers": {
            "answer": {
                "type": "choice",
                "choice": choice,
                "probabilities": probabilities,
                "confidence": confidence if confidence is not None else max(probabilities.values()),
            }
        }
    }


def score_response(score, probabilities, confidence=0.7):
    return {
        "answers": {"answer": {"type": "score", "score": score, "probabilities": probabilities, "confidence": confidence}}
    }


class BuildQuestionsTest(unittest.TestCase):
    def test_noul_uses_the_question_as_instructions(self):
        item = {"kind": "noul", "question": "Is this a billing dispute?"}
        questions = build_questions(item)
        self.assertEqual(questions["answer"]["type"], "noul")
        self.assertEqual(questions["answer"]["instructions"], "Is this a billing dispute?")

    def test_choice_passes_instructions_when_given(self):
        item = {"kind": "choice", "criteria": {"a": "A", "b": "B"}, "instructions": "Rule A wins."}
        self.assertEqual(build_questions(item)["answer"]["instructions"], "Rule A wins.")

    def test_choice_defaults_instructions_when_absent(self):
        item = {"kind": "choice", "criteria": {"a": "A"}}
        self.assertIn("best option", build_questions(item)["answer"]["instructions"])

    def test_score_keeps_criteria_order(self):
        item = {"kind": "score", "question": "What is 2 + 2?", "criteria": ["3", "4", "5"]}
        self.assertEqual(build_questions(item)["answer"]["criteria"], ["3", "4", "5"])

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            build_questions({"kind": "ranking"})


class ClosestLevelTest(unittest.TestCase):
    def test_rounds_to_nearest_index_and_clamps(self):
        levels = ["a", "b", "c"]
        self.assertEqual(closest_level(0.0, levels), "a")
        self.assertEqual(closest_level(1.4, levels), "b")
        self.assertEqual(closest_level(99.0, levels), "c")


class AnswerSignalsTest(unittest.TestCase):
    def test_noul_gate_is_decision_confidence(self):
        item = {"kind": "noul", "expected": True}
        signals = answer_signals(item, noul_response(0.2))
        self.assertFalse(signals["predicted"])
        self.assertFalse(signals["correct"])
        self.assertAlmostEqual(signals["gate_primary"], 0.8)
        self.assertIsNone(signals["official_confidence"])

    def test_choice_uses_official_confidence_and_margin(self):
        item = {"kind": "choice", "expected": "billing"}
        signals = answer_signals(
            item,
            choice_response("billing", {"billing": 0.6, "network": 0.3, "account": 0.1}, confidence=0.42),
        )
        self.assertTrue(signals["correct"])
        self.assertAlmostEqual(signals["gate_primary"], 0.42)
        self.assertAlmostEqual(signals["gate_topprob"], 0.6)
        self.assertAlmostEqual(signals["gate_margin"], 0.3)

    def test_choice_falls_back_to_top_probability_without_confidence(self):
        item = {"kind": "choice", "expected": "a"}
        response = choice_response("a", {"a": 0.9, "b": 0.1})
        del response["answers"]["answer"]["confidence"]
        signals = answer_signals(item, response)
        self.assertAlmostEqual(signals["gate_primary"], 0.9)

    def test_score_snaps_to_the_nearest_level(self):
        item = {"kind": "score", "expected": "115", "criteria": ["100", "110", "115", "120", "130"]}
        signals = answer_signals(item, score_response(2.0, {"2": 0.8}))
        self.assertEqual(signals["predicted"], "115")
        self.assertTrue(signals["correct"])


class GateSweepTest(unittest.TestCase):
    def test_counts_coverage_catch_rate_and_escapes(self):
        rows = [
            {"id": "a", "correct": True, "gate_primary": 0.95},
            {"id": "b", "correct": False, "gate_primary": 0.8},
            {"id": "c", "correct": False, "gate_primary": 0.6},
            {"id": "d", "correct": False, "gate_primary": 0.3},
            {"id": "e", "correct": True, "gate_primary": 0.65},
        ]
        table = gate_sweep(rows, "gate_primary", [0.7])
        row = table[0]
        self.assertEqual(row["accepted_count"], 2)
        self.assertEqual(row["coverage"], 0.4)
        self.assertEqual(row["accepted_accuracy"], 0.5)
        self.assertEqual(row["escalated_count"], 3)
        self.assertEqual(row["escalated_wrong"], 2)
        self.assertEqual(row["escalation_precision"], 2 / 3)
        self.assertEqual(row["errors_caught"], 2)
        self.assertEqual(row["error_catch_rate"], 2 / 3)
        self.assertEqual(row["accepted_error_count"], 1)

    def test_threshold_zero_accepts_everything(self):
        rows = [{"id": "a", "correct": True, "gate_primary": 0.1}]
        row = gate_sweep(rows, "gate_primary", [0.0])[0]
        self.assertEqual(row["coverage"], 1.0)
        self.assertEqual(row["escalated_count"], 0)
        self.assertIsNone(row["escalation_precision"])

    def test_rows_without_the_gate_are_ignored(self):
        rows = [
            {"id": "a", "correct": True, "gate_primary": 0.9},
            {"id": "b", "correct": True, "gate_primary": None},
        ]
        row = gate_sweep(rows, "gate_primary", [0.5])[0]
        self.assertEqual(row["coverage"], 1.0)
        self.assertEqual(row["accepted_count"], 1)


class ContextRotTest(unittest.TestCase):
    def test_pairs_clean_and_padded_items(self):
        rows = [
            {"id": "rot-1-clean", "pair": "rot-1", "correct": True, "gate_primary": 0.9},
            {"id": "rot-1-padded", "pair": "rot-1", "correct": False, "gate_primary": 0.55},
        ]
        pairs = paired_context_rot(rows)
        self.assertEqual(len(pairs), 1)
        self.assertTrue(pairs[0]["degraded"])
        self.assertAlmostEqual(pairs[0]["gate_drop"], 0.35)

    def test_missing_half_is_skipped(self):
        rows = [{"id": "rot-1-clean", "pair": "rot-1", "correct": True, "gate_primary": 0.9}]
        self.assertEqual(paired_context_rot(rows), [])


class DecompositionTest(unittest.TestCase):
    def test_argmax_and_rank(self):
        rows = [
            {
                "id": "dec-1",
                "expected": 3,
                "candidate_probabilities": {"1": 0.1, "2": 0.2, "3": 0.6, "4": 0.1},
            }
        ]
        summary = decomposition_summary(rows)
        self.assertEqual(summary["argmax_accuracy"], 1.0)
        self.assertEqual(summary["mean_rank_of_expected"], 1.0)

    def test_wrong_argmax_is_reported(self):
        rows = [
            {
                "id": "dec-2",
                "expected": 2,
                "candidate_probabilities": {"1": 0.7, "2": 0.2, "3": 0.1},
            }
        ]
        summary = decomposition_summary(rows)
        self.assertEqual(summary["argmax_accuracy"], 0.0)
        self.assertEqual(summary["rows"][0]["argmax"], 1)
        self.assertEqual(summary["rows"][0]["rank_of_expected"], 2)


class PooledGateTest(unittest.TestCase):
    def test_pools_repeated_decisions_per_item(self):
        rows = [
            {"id": "a", "signals": {"correct": False, "gate_primary": 0.2}},
            {"id": "b", "signals": {"correct": True, "gate_primary": 0.9}},
            {"id": "c", "signals": {"correct": True, "gate_primary": 0.95}},
        ]
        indexed = per_item(rows)
        self.assertEqual(len(indexed), 3)
        pooled = {"a": [indexed["a"], indexed["a"]], "b": [indexed["b"], indexed["b"]]}
        row = pooled_gates(pooled, "gate_primary")[0]
        self.assertEqual(row["coverage"], 0.5)
        self.assertEqual(row["errors_caught"], 2)
        self.assertEqual(row["error_catch_rate"], 1.0)
        self.assertEqual(row["escaped_errors"], 0)

    def test_error_free_pool_reports_no_catch_rate(self):
        rows = [{"id": "a", "signals": {"correct": True, "gate_primary": 0.9}}]
        pooled = {"a": [per_item(rows)["a"]]}
        row = pooled_gates(pooled, "gate_primary")[0]
        self.assertIsNone(row["error_catch_rate"])
        self.assertEqual(row["coverage"], 1.0)

    def test_rows_without_signals_are_dropped(self):
        rows = [
            {"id": "a", "signals": {"correct": True, "gate_primary": 0.9}},
            {"id": "b", "error": "HTTP 500"},
        ]
        self.assertEqual(list(per_item(rows)), ["a"])


if __name__ == "__main__":
    unittest.main()

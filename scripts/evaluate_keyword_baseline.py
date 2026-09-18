#!/usr/bin/env python3
"""Evaluate a transparent keyword baseline as a dataset difficulty sanity check."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

try:
    from scripts.evaluate_support import (
        BINARY_FIELDS,
        calculate_metrics,
        load_json,
        load_jsonl,
        render_report,
        validate_cases,
    )
except ModuleNotFoundError:  # Direct execution adds scripts/, not the repository root, to sys.path.
    from evaluate_support import (
        BINARY_FIELDS,
        calculate_metrics,
        load_json,
        load_jsonl,
        render_report,
        validate_cases,
    )


CATEGORY_TERMS = {
    "security": (
        "compromised",
        "attacker",
        "suspicious",
        "intruder",
        "hacked",
        "impersonating",
        "recovery email",
        "security alert",
        "login alert",
    ),
    "network": ("wi-fi", "wifi", "wireless", "network", "vpn", "remote connection"),
    "billing": (
        "charged",
        "charge",
        "billing",
        "subscription",
        "annual plan",
        "monthly plan",
        "refund",
        "payment",
        "renewal",
    ),
    "account": ("password", "reset link", "sign-in", "sign in", "login", "locked out", "account access"),
    "product": ("csv", "import", "upload", "dark mode", "dark theme", "color theme", "feature", "app support"),
}


def contains_any(text: str, terms: Sequence[str]) -> bool:
    return any(term in text for term in terms)


def classify_category(text: str) -> str:
    lowered = text.lower()
    for category in ("security", "network", "billing", "account", "product"):
        if contains_any(lowered, CATEGORY_TERMS[category]):
            return category
    return "other"


def classify_urgent(text: str) -> bool:
    lowered = text.lower()
    if contains_any(lowered, ("not urgent", "not an emergency", "no immediate deadline", "can wait")):
        return False
    return contains_any(
        lowered,
        (
            "in 20 minutes",
            "starts shortly",
            "begins at",
            "in one hour",
            "before noon",
            "deadline is today",
            "right now",
            "immediately",
            "urgent security",
            "tomorrow",
            "today",
        ),
    )


def classify_needs_human(text: str) -> bool:
    lowered = text.lower()
    return contains_any(
        lowered,
        (
            "payroll administrator",
            "admin login",
            "payroll owner",
            "charged twice",
            "two completed card charges",
            "billed me twice",
            "compromised",
            "unknown person",
            "attacker",
            "pending for three weeks",
            "refund still has not arrived",
            "three weeks late",
        ),
    )


def classify_missing_info(text: str) -> bool:
    lowered = text.lower()
    return contains_any(
        lowered,
        (
            "vpn does not work",
            "all the information i have",
            "do not know the error",
            "it is broken",
            "nothing works",
            "will not provide any details",
        ),
    )


def score_frustration(text: str) -> int:
    lowered = text.lower()
    if contains_any(lowered, ("useless", "furious", "unacceptable", "idiot")):
        return 2
    if contains_any(
        lowered,
        (
            "frustrated",
            "irritated",
            "annoyed",
            "please escalate",
            "lock it now",
            "blocks salary",
            "losing sales",
        ),
    ):
        return 1
    return 0


def choice_answer(choice: str, labels: Sequence[str], confidence: float = 0.85) -> Dict[str, Any]:
    remainder = (1.0 - confidence) / (len(labels) - 1)
    probabilities = {label: remainder for label in labels}
    probabilities[choice] = confidence
    return {
        "type": "choice",
        "choice": choice,
        "probabilities": probabilities,
        "confidence": confidence,
    }


def score_answer(score: int, levels: int = 3, confidence: float = 0.85) -> Dict[str, Any]:
    remainder = (1.0 - confidence) / (levels - 1)
    probabilities = {str(index): remainder for index in range(levels)}
    probabilities[str(score)] = confidence
    weighted = sum(index * probability for index, probability in enumerate(probabilities.values()))
    return {
        "type": "score",
        "score": weighted,
        "probabilities": probabilities,
        "confidence": confidence,
        "legend": {"0": "calm", "1": "frustrated", "2": "angry"},
    }


def evaluate_case(case: Mapping[str, Any], categories: Sequence[str]) -> Dict[str, Any]:
    state = case["state"]
    category = classify_category(state)
    binary = {
        "urgent": classify_urgent(state),
        "needs_human": classify_needs_human(state),
        "missing_info": classify_missing_info(state),
    }
    answers: Dict[str, Any] = {"category": choice_answer(category, categories)}
    for field in BINARY_FIELDS:
        answers[field] = {"type": "noul", "noul": 0.85 if binary[field] else 0.15}
    answers["frustration"] = score_answer(score_frustration(state))
    return {
        "id": case["id"],
        "group": case.get("group", case["id"]),
        "state": state,
        "expected": case["expected"],
        "latency_ms": 0.0,
        "attempts": 1,
        "response": {
            "model": "keyword-baseline-v1",
            "answers": answers,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("evals/support-routing-v1.jsonl"))
    parser.add_argument("--questions", type=Path, default=Path("evals/support-routing-v1.questions.json"))
    parser.add_argument("--run-name", default="support-routing-v1-keyword-baseline")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()

    questions = load_json(args.questions)
    cases = load_jsonl(args.cases)
    categories = list(questions["category"]["criteria"])
    validate_cases(cases, categories)
    results = [evaluate_case(case, categories) for case in cases]
    now = datetime.now(timezone.utc).isoformat()
    run = {
        "dataset": str(args.cases),
        "questions": str(args.questions),
        "requested_model": "keyword-baseline-v1",
        "started_at": now,
        "finished_at": now,
        "results": results,
        "metrics": calculate_metrics(results, categories),
        "warning": "This baseline was written after inspecting the task definition and is only a difficulty sanity check.",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"{args.run_name}.json"
    report_path = args.output_dir / f"{args.run_name}.md"
    json_path.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = render_report(run)
    report += (
        "\n## 基线限制\n\n"
        "该基线在查看任务定义和测试样例后编写，存在明显的数据集适配，不是与 Jev 公平竞争的模型。"
        "它只用于检查当前测试集是否能被简单词法规则解决。\n"
    )
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

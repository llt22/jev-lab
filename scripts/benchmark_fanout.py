#!/usr/bin/env python3
"""Measure Jev latency and token usage as the number of parallel questions grows."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.evaluate_support import load_dotenv_key, percentile, request_evaluation
except ModuleNotFoundError:
    from evaluate_support import load_dotenv_key, percentile, request_evaluation


INPUT_PRICE_PER_MILLION = 0.042
STATE = {
    "message": (
        "Our payroll administrator cannot sign in after a password reset. Payroll must be submitted "
        "before noon today, and employees may be paid late if access is not restored. The user sees "
        "error AUTH-403 on Chrome and Safari. Other administrators can still sign in."
    ),
    "account_tier": "enterprise",
    "recent_events": ["password reset requested", "reset completed", "AUTH-403 on next login"],
}

QUESTION_TEXTS = [
    "Does the message describe concrete urgency?",
    "Is account access the primary issue?",
    "Is a human specialist required?",
    "Is essential diagnostic information missing?",
    "Is there immediate business impact?",
    "Is this primarily a billing problem?",
    "Is this primarily a network problem?",
    "Is this an active security compromise?",
    "Does the user appear strongly angry?",
    "Is identity verification likely required?",
    "Could routine troubleshooting alone resolve this?",
    "Is a concrete error code present?",
    "Is more than one user affected?",
    "Is there a stated deadline?",
    "Would delay risk financial harm?",
    "Is the issue reproducible across browsers?",
    "Is the request a feature request?",
    "Should automation avoid changing account permissions?",
    "Is escalation more appropriate than self-service guidance?",
    "Does the message contain enough information to begin investigation?",
]


def questions(count: int):
    return {
        f"q{index + 1:02d}": {"type": "noul", "instructions": text}
        for index, text in enumerate(QUESTION_TEXTS[:count])
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", default="1,5,10,20")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--model", default="jev-1.13.0")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/fanout-jev-1.13.0-2026-09-18.json"))
    args = parser.parse_args()

    counts = [int(value) for value in args.counts.split(",")]
    if any(count < 1 or count > len(QUESTION_TEXTS) for count in counts):
        parser.error(f"counts must be between 1 and {len(QUESTION_TEXTS)}")
    load_dotenv_key(args.env_file)
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        parser.error("TYPESAFE_API_KEY is not set")

    runs = []
    for count in counts:
        for repeat in range(1, args.repeats + 1):
            print(f"questions={count} repeat={repeat}/{args.repeats}", flush=True)
            evaluation = request_evaluation(
                api_key=api_key,
                state=STATE,
                questions=questions(count),
                model=args.model,
                timeout=30.0,
                max_attempts=4,
            )
            usage = evaluation["response"].get("usage", {})
            runs.append(
                {
                    "question_count": count,
                    "repeat": repeat,
                    "latency_ms": evaluation["latency_ms"],
                    "input_tokens": int(usage.get("input_tokens", 0)),
                    "output_tokens": int(usage.get("output_tokens", 0)),
                    "model": evaluation["response"].get("model"),
                }
            )
            time.sleep(0.15)

    summary = []
    for count in counts:
        members = [run for run in runs if run["question_count"] == count]
        latencies = [run["latency_ms"] for run in members]
        inputs = [run["input_tokens"] for run in members]
        outputs = [run["output_tokens"] for run in members]
        mean_input = statistics.fmean(inputs)
        summary.append(
            {
                "question_count": count,
                "latency_mean_ms": statistics.fmean(latencies),
                "latency_p50_ms": percentile(latencies, 0.5),
                "latency_max_ms": max(latencies),
                "input_tokens_mean": mean_input,
                "output_tokens_mean": statistics.fmean(outputs),
                "estimated_cost_usd_per_request": mean_input / 1_000_000 * INPUT_PRICE_PER_MILLION,
            }
        )

    artifact = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requested_model": args.model,
        "input_price_per_million_usd": INPUT_PRICE_PER_MILLION,
        "repeats": args.repeats,
        "runs": runs,
        "summary": summary,
    }
    args.output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    report_path = args.output.with_suffix(".md")
    lines = [
        "# Jev Fan-out 基准",
        "",
        f"> 模型：`{args.model}`",
        f"> 每个问题数重复：{args.repeats} 次",
        "",
        "| 问题数 | 平均延迟 | P50 延迟 | 最大延迟 | 平均输入 token | 平均输出 token | 估算单次成本 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summary:
        lines.append(
            f"| {item['question_count']} | {item['latency_mean_ms']:.0f} ms | "
            f"{item['latency_p50_ms']:.0f} ms | {item['latency_max_ms']:.0f} ms | "
            f"{item['input_tokens_mean']:.0f} | {item['output_tokens_mean']:.0f} | "
            f"${item['estimated_cost_usd_per_request']:.6f} |"
        )
    lines.extend(
        [
            "",
            "该测试只衡量同一短状态下增加 Noul 问题数量的端到端表现，不代表长上下文、Choice、Score 或高并发场景。",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Probe a streaming reasoning model with an optional Jev interruption loop."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    from scripts.evaluate_support import request_evaluation
except ModuleNotFoundError:
    from evaluate_support import request_evaluation


ENV_NAMES = (
    "TYPESAFE_API_KEY", "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL", "DEEPSEEK_REASONING_EFFORT",
)
SYSTEM_PROMPT = "Work carefully and verify the answer before responding. The final answer must follow the user's requested format."
SUPERVISOR_QUESTIONS = {
    "action": {
        "type": "choice",
        "instructions": (
            "Given the user's simple task and the partial live reasoning, choose whether to let reasoning continue "
            "or interrupt it and ask for a final answer now. Only choose answer_now when the solution is already "
            "clear and further analysis is unnecessary. Never use confidence as proof of correctness."
        ),
        "criteria": {
            "continue": "A substantive unresolved step or uncertainty remains.",
            "answer_now": "The answer is already clear; further thinking repeats or complicates it.",
        },
    },
    "needs_more": {
        "type": "noul",
        "instructions": "Does this task still require substantive reasoning or verification before a safe final answer?",
    },
}


def load_config(path: Path) -> dict[str, str]:
    config = {name: os.environ.get(name, "") for name in ENV_NAMES}
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name = name.strip()
            if name not in config or config[name]:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            config[name] = value
    missing = [name for name, value in config.items() if not value]
    if missing:
        raise ValueError("missing configuration: " + ", ".join(missing))
    return config


def chat_url(base: str) -> str:
    base = base.rstrip("/")
    return base if base.endswith("/chat/completions") else base + "/chat/completions"


def parse_event(line: bytes) -> Mapping[str, Any] | None:
    if not line.startswith(b"data:"):
        return None
    data = line[5:].strip()
    if data == b"[DONE]":
        return None
    event = json.loads(data)
    if not isinstance(event, dict):
        raise ValueError("stream event must be an object")
    if event.get("success") is False:
        raise RuntimeError("provider reported an unsuccessful stream event (body omitted)")
    return event.get("data", event)


def should_interrupt(answer: Mapping[str, Any], threshold: float) -> bool:
    action = answer["action"]
    return (
        action.get("choice") == "answer_now"
        and float(action.get("probabilities", {}).get("answer_now", 0)) >= threshold
        and float(answer["needs_more"]["noul"]) <= 1 - threshold
    )


def normalized_answer(value: str) -> str:
    return re.sub(r"[\s.!?]+$", "", value.strip()).lower()


def judge(api_key: str, question: str, excerpt: str) -> dict[str, Any]:
    result = request_evaluation(
        api_key,
        json.dumps({"user_task": question, "partial_reasoning": excerpt[-1800:]}, ensure_ascii=False),
        SUPERVISOR_QUESTIONS,
        "jev-latest",
        12,
        1,
    )
    answers = result["response"]["answers"]
    return {
        "answer": answers,
        "latency_ms": result["latency_ms"],
        "usage": result["response"].get("usage"),
    }


def stream_chat(
    config: Mapping[str, str], question: str, mode: str, threshold: float,
    max_tokens: int, min_reasoning_chars: int,
    resumed: bool = False,
) -> dict[str, Any]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    if resumed:
        messages.append({"role": "user", "content": "The previous attempt was interrupted. Answer the original question directly now; do not repeat exploratory analysis."})
    payload = {
        "model": config["DEEPSEEK_MODEL"], "messages": messages,
        "reasoning_effort": config["DEEPSEEK_REASONING_EFFORT"],
        "max_tokens": max_tokens, "stream": True,
        "stream_options": {"include_usage": True},
    }
    request = urllib.request.Request(
        chat_url(config["DEEPSEEK_BASE_URL"]),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + config["DEEPSEEK_API_KEY"], "Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    reasoning: list[str] = []
    content: list[str] = []
    checks: list[dict[str, Any]] = []
    interrupted = False
    finish_reason = None
    usage = None
    stream_elapsed_ms = None
    pending: Future[dict[str, Any]] | None = None
    last_checked_chars = 0
    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                if "text/event-stream" not in response.headers.get("Content-Type", ""):
                    raise ValueError("provider did not return an SSE stream")
                for line in response:
                    event = parse_event(line)
                    if event is None:
                        continue
                    if event.get("usage"):
                        usage = event["usage"]
                    for choice in event.get("choices") or []:
                        delta = choice.get("delta") or {}
                        reason = delta.get("reasoning") or delta.get("reasoning_content")
                        if isinstance(reason, str):
                            reasoning.append(reason)
                        text = delta.get("content")
                        if isinstance(text, str):
                            content.append(text)
                        if choice.get("finish_reason"):
                            finish_reason = choice["finish_reason"]
                    length = sum(map(len, reasoning))
                    if pending is not None and pending.done():
                        try:
                            verdict = pending.result()
                            answers = verdict["answer"]
                            stop = should_interrupt(answers, threshold)
                            checks.append({
                                "at_ms": round((time.perf_counter() - started) * 1000),
                                "reasoning_chars": last_checked_chars,
                                "action": answers["action"]["choice"],
                                "answer_now_probability": answers["action"]["probabilities"].get("answer_now"),
                                "needs_more_probability": answers["needs_more"]["noul"],
                                "jev_latency_ms": verdict["latency_ms"],
                                "would_interrupt": stop,
                            })
                            if mode == "intervene" and stop and not content:
                                interrupted = True
                                break
                        except Exception as exc:
                            checks.append({"error": type(exc).__name__, "at_ms": round((time.perf_counter() - started) * 1000)})
                        pending = None
                    if (
                        mode != "baseline" and not resumed and pending is None and len(checks) < 2
                        and length >= min_reasoning_chars and length - last_checked_chars >= min_reasoning_chars
                    ):
                        last_checked_chars = length
                        pending = pool.submit(judge, config["TYPESAFE_API_KEY"], question, "".join(reasoning)[-1800:])
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"provider HTTP {exc.code} (body omitted)") from exc
        stream_elapsed_ms = round((time.perf_counter() - started) * 1000)
        if pending is not None:
            try:
                verdict = pending.result(timeout=15)
                answers = verdict["answer"]
                checks.append({
                    "at_ms": round((time.perf_counter() - started) * 1000),
                    "reasoning_chars": last_checked_chars,
                    "action": answers["action"]["choice"],
                    "answer_now_probability": answers["action"]["probabilities"].get("answer_now"),
                    "needs_more_probability": answers["needs_more"]["noul"],
                    "jev_latency_ms": verdict["latency_ms"],
                    "would_interrupt": should_interrupt(answers, threshold),
                    "too_late": True,
                })
            except Exception as exc:
                checks.append({"error": type(exc).__name__, "too_late": True})
    return {
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "stream_elapsed_ms": stream_elapsed_ms,
        "reasoning_chars": sum(map(len, reasoning)),
        "content": "".join(content),
        "finish_reason": finish_reason,
        "usage": usage,
        "checks": checks,
        "interrupted": interrupted,
    }


def evaluate_case(config: Mapping[str, str], case: Mapping[str, str], mode: str, args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    initial = stream_chat(config, case["question"], mode, args.threshold, args.max_tokens, args.min_reasoning_chars)
    resumed = None
    if initial["interrupted"]:
        resumed = stream_chat(config, case["question"], "baseline", args.threshold, args.max_tokens, args.min_reasoning_chars, resumed=True)
    final = resumed or initial
    return {
        "id": case["id"], "mode": mode,
        "correct": normalized_answer(final["content"]) == normalized_answer(case["expected"]),
        "answer_ready_ms": initial["stream_elapsed_ms"] + (resumed["stream_elapsed_ms"] if resumed else 0),
        "final_answer": final["content"].strip()[:300],
        "total_elapsed_ms": round((time.perf_counter() - started) * 1000),
        "initial": initial, "resumed": resumed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("evals/thinking-supervision-v1.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/thinking-supervision-v1.json"))
    parser.add_argument("--modes", nargs="+", choices=("baseline", "observe", "intervene"), default=["baseline", "observe", "intervene"])
    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--min-reasoning-chars", type=int, default=300)
    parser.add_argument("--max-tokens", type=int, default=4096)
    args = parser.parse_args()
    if not 0.5 < args.threshold <= 1 or args.min_reasoning_chars < 1 or args.max_tokens < 1:
        parser.error("threshold must be in (0.5, 1]; budgets must be positive")
    cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        parser.error("dataset must be a nonempty list")
    config = load_config(Path(".env"))
    report: dict[str, Any] = {"created_at": datetime.now(timezone.utc).isoformat(), "model": config["DEEPSEEK_MODEL"], "threshold": args.threshold, "rows": []}
    for case in cases:
        for mode in args.modes:
            print(f"{case['id']} {mode}", flush=True)
            try:
                row = evaluate_case(config, case, mode, args)
                row["initial"].pop("content")
                if row["resumed"]:
                    row["resumed"].pop("content")
            except Exception as exc:
                row = {"id": case["id"], "mode": mode, "error": f"{type(exc).__name__}: {exc}"}
            report["rows"].append(row)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  {'error' if 'error' in row else 'correct=' + str(row['correct']) + ' elapsed_ms=' + str(row['total_elapsed_ms'])}", flush=True)


if __name__ == "__main__":
    main()

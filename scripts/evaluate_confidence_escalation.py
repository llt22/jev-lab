#!/usr/bin/env python3
"""Test whether Jev confidence can gate a cheap-first / strong-model-second cascade.

The dataset targets failure modes TypeSafe documents itself in
`docs.typesafe.ai/model-jaggedness/jev-1.13` (negation, indirection, numeric
precision, context rot, contradictory instructions) next to a clear baseline.
Every item has ground truth that is checkable without another model, so Jev is
scored against facts rather than against a second model's opinion.

The escalation decision is made by deterministic code from the returned
probability distribution; Jev never decides its own escalation.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

try:
    from scripts.evaluate_support import request_evaluation
except ModuleNotFoundError:  # Direct execution from inside scripts/.
    from evaluate_support import request_evaluation


DEFAULT_DATASET = Path("evals/confidence-escalation-v1.json")
DEFAULT_MODEL = "jev-latest"
INPUT_PRICE_PER_MTOK = 0.042  # docs.typesafe.ai/models, 2026-09-18: output tokens are free.
GATE_KEYS = ("gate_primary", "gate_topprob")
GROUP_ORDER = ("clear", "negation", "indirection", "numeric", "context_rot", "contradictory")


def load_dataset(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        dataset = json.load(handle)
    if not isinstance(dataset, Mapping) or not isinstance(dataset.get("items"), list):
        raise ValueError("dataset must be an object with an items list")
    return dict(dataset)


def build_questions(item: Mapping[str, Any]) -> Dict[str, Any]:
    """Map one dataset item onto the Jev question schema."""
    kind = item["kind"]
    if kind == "choice":
        question: Dict[str, Any] = {
            "type": "choice",
            "criteria": dict(item["criteria"]),
        }
        if item.get("instructions"):
            question["instructions"] = item["instructions"]
        else:
            question["instructions"] = "Choose the single best option for this message."
        return {"answer": question}
    if kind == "noul":
        return {
            "answer": {
                "type": "noul",
                "instructions": item["question"],
            }
        }
    if kind == "score":
        return {
            "answer": {
                "type": "score",
                "instructions": item["question"],
                "criteria": list(item["criteria"]),
            }
        }
    raise ValueError(f"unknown item kind {kind!r}")


def closest_level(score: float, levels: Sequence[str]) -> str:
    """Score answers may land between levels; pick the nearest one by index."""
    index = min(max(int(round(score)), 0), len(levels) - 1)
    return levels[index]


def answer_signals(item: Mapping[str, Any], response: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract the decision plus every gate signal from one Jev answer."""
    answer = response["answers"]["answer"]
    kind = item["kind"]
    signals: Dict[str, Any] = {"kind": kind}

    if kind == "noul":
        probability = float(answer["noul"])
        signals.update(
            predicted=probability >= 0.5,
            gate_primary=max(probability, 1.0 - probability),
            gate_topprob=max(probability, 1.0 - probability),
            probability=probability,
            official_confidence=None,
        )
    elif kind == "choice":
        probabilities = {label: float(value) for label, value in answer["probabilities"].items()}
        ordered = sorted(probabilities.values(), reverse=True)
        top = ordered[0]
        second = ordered[1] if len(ordered) > 1 else 0.0
        signals.update(
            predicted=answer["choice"],
            gate_primary=float(answer.get("confidence", top)),
            gate_topprob=top,
            gate_margin=top - second,
            official_confidence=float(answer.get("confidence", top)),
            probabilities=probabilities,
        )
    elif kind == "score":
        probabilities = {str(label): float(value) for label, value in answer.get("probabilities", {}).items()}
        ordered = sorted(probabilities.values(), reverse=True)
        top = ordered[0] if ordered else 0.0
        second = ordered[1] if len(ordered) > 1 else 0.0
        levels = list(item["criteria"])
        signals.update(
            predicted=closest_level(float(answer["score"]), levels),
            raw_score=float(answer["score"]),
            gate_primary=float(answer.get("confidence", top)),
            gate_topprob=top,
            gate_margin=top - second,
            official_confidence=float(answer.get("confidence", top)),
            probabilities=probabilities,
        )
    else:
        raise ValueError(f"unknown item kind {kind!r}")

    signals["correct"] = signals["predicted"] == item["expected"]
    return signals


def gate_sweep(
    rows: Sequence[Mapping[str, Any]],
    gate_key: str,
    thresholds: Sequence[float],
) -> List[Dict[str, Any]]:
    """Risk/coverage table for a gate: escalate everything below the threshold."""
    usable = [row for row in rows if row.get(gate_key) is not None]
    total = len(usable)
    if not total:
        return []
    total_errors = sum(1 for row in usable if not row["correct"])
    table: List[Dict[str, Any]] = []
    for threshold in thresholds:
        accepted = [row for row in usable if row[gate_key] >= threshold]
        escalated = [row for row in usable if row[gate_key] < threshold]
        accepted_errors = sum(1 for row in accepted if not row["correct"])
        escalated_errors = sum(1 for row in escalated if not row["correct"])
        table.append(
            {
                "threshold": threshold,
                "coverage": len(accepted) / total,
                "accepted_count": len(accepted),
                "accepted_accuracy": (
                    statistics.fmean(1.0 if row["correct"] else 0.0 for row in accepted) if accepted else None
                ),
                "escalated_count": len(escalated),
                "escalated_wrong": escalated_errors,
                "escalation_precision": (escalated_errors / len(escalated)) if escalated else None,
                "errors_caught": escalated_errors,
                "error_catch_rate": (escalated_errors / total_errors) if total_errors else None,
                "accepted_error_count": accepted_errors,
            }
        )
    return table


def group_accuracy(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    summary: Dict[str, Dict[str, Any]] = {}
    for group in GROUP_ORDER:
        members = [row for row in rows if row["group"] == group]
        if not members:
            continue
        summary[group] = {
            "count": len(members),
            "accuracy": statistics.fmean(1.0 if row["correct"] else 0.0 for row in members),
            "mean_gate": statistics.fmean(row["gate_primary"] for row in members),
            "wrong": [row["id"] for row in members if not row["correct"]],
        }
    return summary


def paired_context_rot(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    by_id = {row["id"]: row for row in rows}
    pairs: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        pair = row.get("pair")
        if not pair or pair in seen:
            continue
        seen.add(pair)
        clean = by_id.get(f"{pair}-clean")
        padded = by_id.get(f"{pair}-padded")
        if not clean or not padded:
            continue
        pairs.append(
            {
                "pair": pair,
                "clean_correct": clean["correct"],
                "padded_correct": padded["correct"],
                "clean_gate": clean["gate_primary"],
                "padded_gate": padded["gate_primary"],
                "gate_drop": clean["gate_primary"] - padded["gate_primary"],
                "degraded": bool(clean["correct"] and not padded["correct"]),
            }
        )
    return pairs


def decomposition_summary(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Does asking 32 isolated Nouls recover a numeric answer the Score misses?"""
    if not rows:
        return {"count": 0}
    results = []
    for row in rows:
        probabilities = row["candidate_probabilities"]
        ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        argmax_value = int(ranked[0][0])
        correct_value = row["expected"]
        rank_of_correct = 1 + [int(value) for value, _ in ranked].index(correct_value)
        results.append(
            {
                "id": row["id"],
                "expected": correct_value,
                "argmax": argmax_value,
                "argmax_correct": argmax_value == correct_value,
                "probability_at_expected": probabilities[str(correct_value)],
                "rank_of_expected": rank_of_correct,
                "candidates": len(probabilities),
            }
        )
    return {
        "count": len(results),
        "argmax_accuracy": statistics.fmean(1.0 if item["argmax_correct"] else 0.0 for item in results),
        "mean_rank_of_expected": statistics.fmean(item["rank_of_expected"] for item in results),
        "rows": results,
    }


def score_run(run: Mapping[str, Any]) -> Dict[str, Any]:
    rows = [row for row in run["rows"] if "signals" in row]
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]
    return {
        "completed": len(rows),
        "errors": sum(1 for row in run["rows"] if "error" in row),
        "accuracy": statistics.fmean(1.0 if row["signals"]["correct"] else 0.0 for row in rows) if rows else 0.0,
        "groups": group_accuracy([{**row["signals"], "id": row["id"], "group": row["group"]} for row in rows]),
        "gates": {
            gate: gate_sweep(
                [{**row["signals"], "id": row["id"]} for row in rows],
                gate,
                thresholds,
            )
            for gate in GATE_KEYS
        },
        "context_rot_pairs": paired_context_rot(
            [{**row["signals"], "id": row["id"], "group": row["group"], "pair": row.get("pair")} for row in rows]
        ),
        "latency_ms": {
            "mean": statistics.fmean(row["latency_ms"] for row in rows) if rows else 0.0,
            "p50": statistics.median([row["latency_ms"] for row in rows]) if rows else 0.0,
            "max": max((row["latency_ms"] for row in rows), default=0.0),
        },
        "usage": {
            "input_tokens": sum(row.get("input_tokens", 0) for row in rows),
            "output_tokens": sum(row.get("output_tokens", 0) for row in rows),
        },
    }


def render_report(run: Mapping[str, Any]) -> str:
    metrics = run["metrics"]
    lines = [
        "# 置信度升级闸门实验（Jev 快筛 + 强模型兜底）",
        "",
        f"> 运行时间：{run['finished_at']}",
        f"> 数据集：`{run['dataset']}`",
        f"> 请求模型：`{run['requested_model']}`",
        f"> 实际模型：`{', '.join(run.get('models', {})) or 'unknown'}`",
        "",
        "## 摘要",
        "",
        f"- 完成 {metrics['completed']} 条，错误 {metrics['errors']} 条。",
        f"- Jev 单模型准确率：{metrics['accuracy'] * 100:.1f}%。",
        f"- 延迟 P50 / 均值 / 最大：{metrics['latency_ms']['p50']:.0f} / "
        f"{metrics['latency_ms']['mean']:.0f} / {metrics['latency_ms']['max']:.0f} ms。",
        f"- 输入 token 合计：{metrics['usage']['input_tokens']}，估算成本 "
        f"${metrics['usage']['input_tokens'] / 1_000_000 * INPUT_PRICE_PER_MTOK:.6f}。",
        "",
        "## 按失效面分组",
        "",
        "| 组 | 样本 | 准确率 | 平均闸门值 | 错例 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for group, item in metrics["groups"].items():
        wrong = ", ".join(item["wrong"]) or "—"
        lines.append(
            f"| `{group}` | {item['count']} | {item['accuracy'] * 100:.1f}% | "
            f"{item['mean_gate']:.3f} | {wrong} |"
        )

    lines.extend(["", "## 闸门扫描（升到强模型）", ""])
    for gate, table in metrics["gates"].items():
        if not table:
            continue
        lines.extend(
            [
                f"### `{gate}`",
                "",
                "| 阈值 | 自动通过率 | 自动通过准确率 | 升级数 | 升级中确为错误 | 错误捕获率 | 漏放错误 |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in table:
            accepted_accuracy = "—" if row["accepted_accuracy"] is None else f"{row['accepted_accuracy'] * 100:.1f}%"
            catch_rate = "—" if row["error_catch_rate"] is None else f"{row['error_catch_rate'] * 100:.0f}%"
            precision = "—" if row["escalation_precision"] is None else f"{row['escalation_precision'] * 100:.0f}%"
            lines.append(
                f"| {row['threshold']:.2f} | {row['coverage'] * 100:.1f}% | {accepted_accuracy} | "
                f"{row['escalated_count']} | {precision} | {catch_rate} | {row['accepted_error_count']} |"
            )
        lines.append("")

    pairs = metrics["context_rot_pairs"]
    if pairs:
        lines.extend(["## 无关上下文对照（同一事实，一段干净一段加料）", ""])
        lines.extend(["| 对照 | 干净版正确 | 加料版正确 | 干净闸门 | 加料闸门 | 闸门下降 |", "| --- | --- | --- | ---: | ---: | ---: |"])
        for pair in pairs:
            lines.append(
                f"| `{pair['pair']}` | {'✅' if pair['clean_correct'] else '❌'} | "
                f"{'✅' if pair['padded_correct'] else '❌'} | {pair['clean_gate']:.3f} | "
                f"{pair['padded_gate']:.3f} | {pair['gate_drop']:+.3f} |"
            )
        lines.append("")

    decomposition = run.get("decomposition")
    if decomposition and decomposition.get("count"):
        lines.extend(
            [
                "## 数字任务的分解对照（1 个 Score vs 32 个 Noul 取最大值）",
                "",
                f"- 分解后 argmax 命中：{decomposition['argmax_accuracy'] * 100:.0f}%（"
                f"{decomposition['count']} 题）。",
                f"- 正确答案在 32 个候选中的平均排名：{decomposition['mean_rank_of_expected']:.1f}。",
                "",
                "| 题 | 正确答案 | 32-Noul argmax | 命中 | 正确答案概率 | 排名 |",
                "| --- | ---: | ---: | --- | ---: | ---: |",
            ]
        )
        for row in decomposition["rows"]:
            lines.append(
                f"| `{row['id']}` | {row['expected']} | {row['argmax']} | "
                f"{'✅' if row['argmax_correct'] else '❌'} | {row['probability_at_expected']:.3f} | "
                f"{row['rank_of_expected']} |"
            )
        lines.append("")

    lines.extend(
        [
            "## 解释限制",
            "",
            "- 这是人工构造的小规模探针，用于验证机制，不是模型质量基准。",
            "- “升级后正确”是上界假设：本实验没有实际调用强模型，只测量闸门能捕获多少错误。",
            "- `confidence` 是概率分布的集中程度，官方明确说明它不等于答对概率，阈值必须在自有数据上校准。",
            "- 每组样本极少，分组准确率的差异不能外推为稳定的能力排序。",
            "",
        ]
    )
    return "\n".join(lines)


def checkpoint(path: Path, run: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", type=Path, default=Path("artifacts/confidence-escalation-v1.json"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--max-attempts", type=int, default=4)
    parser.add_argument("--sleep", type=float, default=0.15)
    parser.add_argument("--skip-decomposition", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset = load_dataset(args.dataset)
    items = dataset["items"]
    if args.limit is not None:
        items = items[: args.limit]

    if args.validate_only:
        ids = [item["id"] for item in items]
        if len(ids) != len(set(ids)):
            raise SystemExit("duplicate item ids")
        for item in items:
            build_questions(item)
        print(f"Validated {len(items)} items and {len(dataset.get('decomposition', []))} decomposition tasks.")
        return 0

    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key and args.env_file.exists():
        for raw in args.env_file.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("TYPESAFE_API_KEY="):
                value = line.split("=", 1)[1].strip().strip("'\"")
                if value:
                    api_key = value
    if not api_key:
        print("TYPESAFE_API_KEY is not set.", file=sys.stderr)
        return 2

    run: Dict[str, Any] = {
        "dataset": str(args.dataset),
        "requested_model": args.model,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "rows": [],
        "decomposition": None,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)

    total = len(items)
    for index, item in enumerate(items, start=1):
        print(f"[{index}/{total}] {item['id']}", flush=True)
        record: Dict[str, Any] = {
            "id": item["id"],
            "group": item["group"],
            "kind": item["kind"],
            "pair": item.get("pair"),
            "expected": item["expected"],
        }
        try:
            evaluation = request_evaluation(
                api_key=api_key,
                state=item["state"],
                questions=build_questions(item),
                model=args.model,
                timeout=args.timeout,
                max_attempts=args.max_attempts,
            )
            response = evaluation["response"]
            record["signals"] = answer_signals(item, response)
            record["latency_ms"] = evaluation["latency_ms"]
            record["attempts"] = evaluation["attempts"]
            record["model"] = response.get("model")
            usage = response.get("usage", {})
            record["input_tokens"] = int(usage.get("input_tokens", 0))
            record["output_tokens"] = int(usage.get("output_tokens", 0))
        except Exception as exc:  # Keep failures visible in the artifact.
            record["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  ERROR: {record['error']}", file=sys.stderr, flush=True)
        run["rows"].append(record)
        checkpoint(args.output, run)
        if args.sleep > 0:
            time.sleep(args.sleep)

    if not args.skip_decomposition:
        for task in dataset.get("decomposition", []):
            start, end = task["candidate_range"]
            candidates = list(range(start, end + 1))
            questions = {
                f"is_{value}": {
                    "type": "noul",
                    "instructions": f"{task['question']} Is the answer exactly {value}?",
                }
                for value in candidates
            }
            print(f"[decomposition] {task['id']} ({len(candidates)} candidates)", flush=True)
            try:
                evaluation = request_evaluation(
                    api_key=api_key,
                    state=task["state"],
                    questions=questions,
                    model=args.model,
                    timeout=args.timeout,
                    max_attempts=args.max_attempts,
                )
                answers = evaluation["response"]["answers"]
                probabilities = {str(value): float(answers[f"is_{value}"]["noul"]) for value in candidates}
                decomposition = run["decomposition"] or {"rows": [], "usage": {"input_tokens": 0, "output_tokens": 0}}
                decomposition["rows"].append(
                    {
                        "id": task["id"],
                        "expected": task["expected"],
                        "candidate_probabilities": probabilities,
                        "latency_ms": evaluation["latency_ms"],
                    }
                )
                usage = evaluation["response"].get("usage", {})
                decomposition["usage"]["input_tokens"] += int(usage.get("input_tokens", 0))
                decomposition["usage"]["output_tokens"] += int(usage.get("output_tokens", 0))
                run["decomposition"] = decomposition
            except Exception as exc:
                print(f"  ERROR: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
            checkpoint(args.output, run)

    if run["decomposition"]:
        run["decomposition"] = {
            **{key: value for key, value in run["decomposition"].items() if key != "rows"},
            **decomposition_summary(run["decomposition"]["rows"]),
        }

    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    run["models"] = {str(row.get("model")): 1 for row in run["rows"] if row.get("model")}
    run["metrics"] = score_run(run)
    checkpoint(args.output, run)

    report_path = args.report or args.output.with_suffix(".md")
    report_path.write_text(render_report(run), encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Wrote {report_path}")
    return 1 if run["metrics"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

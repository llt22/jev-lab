#!/usr/bin/env python3
"""Compare repeated runs of the confidence-escalation probe.

Reports decision flips, gate drift, a pooled gate sweep across every repeated
decision, and whether decomposing a numeric judgement into many narrow Nouls
was more stable than asking it as one Score question.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95)


def load_runs(paths: Sequence[Path]) -> List[Dict[str, Any]]:
    runs = []
    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            runs.append(json.load(handle))
    if not runs:
        raise SystemExit("at least one run is required")
    return runs


def per_item(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    return {row["id"]: row for row in rows if "signals" in row}


def pooled_gates(items: Mapping[str, Sequence[Mapping[str, Any]]], gate_key: str) -> List[Dict[str, Any]]:
    """Pool every repeated decision for one item into a single gate table."""
    table = []
    total = sum(len(entries) for entries in items.values())
    if not total:
        return table
    total_errors = sum(1 for entries in items.values() for row in entries if not row["signals"]["correct"])
    for threshold in THRESHOLDS:
        accepted = [
            row for entries in items.values() for row in entries if row["signals"][gate_key] >= threshold
        ]
        escalated = [
            row for entries in items.values() for row in entries if row["signals"][gate_key] < threshold
        ]
        escalated_errors = sum(1 for row in escalated if not row["signals"]["correct"])
        accepted_errors = sum(1 for row in accepted if not row["signals"]["correct"])
        table.append(
            {
                "threshold": threshold,
                "coverage": len(accepted) / total,
                "accepted_accuracy": (
                    statistics.fmean(1.0 if row["signals"]["correct"] else 0.0 for row in accepted)
                    if accepted
                    else None
                ),
                "escalated_count": len(escalated),
                "escalated_wrong": escalated_errors,
                "escalation_precision": (escalated_errors / len(escalated)) if escalated else None,
                "errors_caught": escalated_errors,
                "error_catch_rate": (escalated_errors / total_errors) if total_errors else None,
                "escaped_errors": accepted_errors,
            }
        )
    return table


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, default=Path("artifacts/confidence-escalation-v1-repeat-stability.md"))
    args = parser.parse_args()

    runs = load_runs(args.runs)
    labels = [path.name for path in args.runs]
    indexed = [per_item(run["rows"]) for run in runs]
    common_ids = [case_id for case_id in indexed[0] if all(case_id in item for item in indexed)]

    lines: List[str] = [
        "# 置信度升级闸门实验：三轮重复稳定性",
        "",
        f"> 对比运行：{', '.join(f'`{label}`' for label in labels)}",
        "",
        "## 每轮总体结果",
        "",
        "| 运行 | 准确率 | 接口错误 | 分解 argmax | 延迟 P50 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, run in zip(labels, runs):
        metrics = run["metrics"]
        argmax = (run.get("decomposition") or {}).get("argmax_accuracy")
        lines.append(
            f"| `{label}` | {metrics['accuracy'] * 100:.1f}% | {metrics['errors']} | "
            f"{'—' if argmax is None else f'{argmax * 100:.0f}%'} | {metrics['latency_ms']['p50']:.0f} ms |"
        )

    flips = []
    spans = []
    for case_id in common_ids:
        predictions = [str(indexed[i][case_id]["signals"]["predicted"]) for i in range(len(runs))]
        gates = [float(indexed[i][case_id]["signals"]["gate_primary"]) for i in range(len(runs))]
        if len(set(predictions)) > 1:
            flips.append({"id": case_id, "predictions": predictions, "gates": gates})
        spans.append({"id": case_id, "span": max(gates) - min(gates), "gates": gates})

    total_decisions = len(common_ids) * len(runs)
    lines.extend(
        [
            "",
            "## 决策一致性",
            "",
            f"- 重复决策总数：{total_decisions}（{len(common_ids)} 条 × {len(runs)} 轮）。",
            f"- 发生翻转的条目：{len(flips)} 条。",
            f"- 决策一致率：{(total_decisions - sum(len(set(f['predictions'])) - 1 for f in flips)) / total_decisions * 100:.1f}%。",
            f"- 平均闸门波动：{statistics.fmean(s['span'] for s in spans):.4f}，"
            f"最大 {max(s['span'] for s in spans):.3f}。",
            "",
        ]
    )
    if flips:
        lines.extend(["### 翻转条目", "", "| 条目 | 各轮预测 | 各轮闸门 |", "| --- | --- | --- |"])
        for flip in flips:
            lines.append(
                f"| `{flip['id']}` | {' / '.join(flip['predictions'])} | "
                f"{' / '.join(f'{gate:.3f}' for gate in flip['gates'])} |"
            )
        lines.append("")

    largest = sorted(spans, key=lambda item: -item["span"])[:5]
    lines.extend(["### 闸门波动最大的条目", "", "| 条目 | 波动 | 各轮闸门 |", "| --- | ---: | --- |"])
    for span in largest:
        lines.append(
            f"| `{span['id']}` | {span['span']:.3f} | {' / '.join(f'{gate:.3f}' for gate in span['gates'])} |"
        )

    lines.extend(["", "## 合并三轮后的闸门扫描", ""])
    pooled = {case_id: [indexed[i][case_id] for i in range(len(runs))] for case_id in common_ids}
    for gate_key in ("gate_primary", "gate_topprob"):
        table = pooled_gates(pooled, gate_key)
        if not table:
            continue
        lines.extend(
            [
                f"### `{gate_key}`",
                "",
                "| 阈值 | 自动通过率 | 自动通过准确率 | 升级数 | 升级中确为错误 | 错误捕获率 | 漏放错误 |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in table:
            accepted = "—" if row["accepted_accuracy"] is None else f"{row['accepted_accuracy'] * 100:.1f}%"
            catch = "—" if row["error_catch_rate"] is None else f"{row['error_catch_rate'] * 100:.0f}%"
            precision = "—" if row["escalation_precision"] is None else f"{row['escalation_precision'] * 100:.0f}%"
            lines.append(
                f"| {row['threshold']:.2f} | {row['coverage'] * 100:.1f}% | {accepted} | "
                f"{row['escalated_count']} | {precision} | {catch} | {row['escaped_errors']} |"
            )
        lines.append("")

    decomposed: Dict[str, List[Any]] = defaultdict(list)
    for run in runs:
        for row in ((run.get("decomposition") or {}).get("rows") or []):
            decomposed[row["id"]].append(row["argmax"] == row["expected"])

    if decomposed:
        lines.extend(
            [
                "## 分解对照：1 个 Score vs 32 个 Noul",
                "",
                "| 题 | 各轮 Score 判定 | 各轮 32-Noul argmax 命中 |",
                "| --- | --- | --- |",
            ]
        )
        for task in sorted(decomposed):
            score_decisions = []
            for index in indexed:
                for case_id, row in index.items():
                    if case_id == f"num-{task.split('-')[1]}":
                        score_decisions.append(str(row["signals"]["predicted"]))
            hits = ["✅" if hit else "❌" for hit in decomposed[task]]
            lines.append(
                f"| `{task}` | {' / '.join(score_decisions) if score_decisions else '—'} | {' / '.join(hits)} |"
            )
        lines.append("")

    lines.extend(
        [
            "## 解释限制",
            "",
            "- 三轮相同输入，只检验可重复性，不覆盖模型版本升级或输入改写。",
            "- 合并后的闸门表把同一批样本重复计数，用于观察机制，不能当作独立样本量的统计结果。",
            "- 每条目的翻转都可能是真实边界样例，也可能只是概率接近阈值；需要更多样本才能区分。",
            "",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
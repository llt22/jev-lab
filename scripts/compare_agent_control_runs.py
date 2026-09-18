#!/usr/bin/env python3
"""Compare decision stability across repeated agent-control benchmark runs."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows_by_id(run, section):
    return {row["id"]: row for row in run[section]["rows"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(args.runs) < 2:
        parser.error("provide at least two runs")

    runs = [load(path) for path in args.runs]
    context_maps = [rows_by_id(run, "context_filtering") for run in runs]
    path_maps = [rows_by_id(run, "semantic_pathfinding") for run in runs]
    route_maps = [rows_by_id(run, "model_routing") for run in runs]

    context_total = 0
    context_stable = 0
    context_ranges = []
    context_flips = []
    for case_id in sorted(set.intersection(*(set(rows) for rows in context_maps))):
        question_ids = sorted(context_maps[0][case_id]["response"]["answers"])
        for question_id in question_ids:
            values = [float(rows[case_id]["response"]["answers"][question_id]["noul"]) for rows in context_maps]
            decisions = [value >= 0.5 for value in values]
            context_total += 1
            context_ranges.append(max(values) - min(values))
            if len(set(decisions)) == 1:
                context_stable += 1
            else:
                context_flips.append({"item": f"{case_id}:{question_id}", "values": values})

    def choice_stability(maps, answer_id):
        common = sorted(set.intersection(*(set(rows) for rows in maps)))
        stable = 0
        flips = []
        for case_id in common:
            choices = [rows[case_id]["response"]["answers"][answer_id]["choice"] for rows in maps]
            if len(set(choices)) == 1:
                stable += 1
            else:
                flips.append({"id": case_id, "choices": choices})
        return len(common), stable, flips

    path_total, path_stable, path_flips = choice_stability(path_maps, "path")
    route_total, route_stable, route_flips = choice_stability(route_maps, "route")
    lines = [
        "# Jev Agent 控制面重复运行稳定性",
        "",
        f"> 运行数：{len(runs)}",
        "",
        "| 输出 | 决策一致率 | 数值平均极差 | 数值最大极差 |",
        "| --- | ---: | ---: | ---: |",
        f"| 上下文 Keep Noul | {context_stable / context_total:.1%} | {statistics.fmean(context_ranges):.4f} | {max(context_ranges):.4f} |",
        f"| 语义路径 Choice | {path_stable / path_total:.1%} | 不适用 | 不适用 |",
        f"| 模型路由 Choice | {route_stable / route_total:.1%} | 不适用 | 不适用 |",
        "",
        "## 决策翻转",
        "",
    ]
    if context_flips:
        for item in context_flips:
            values = ", ".join(f"{value:.2f}" for value in item["values"])
            lines.append(f"- 上下文 `{item['item']}`：{values}。")
    if path_flips:
        for item in path_flips:
            lines.append(f"- 语义路径 `{item['id']}`：{', '.join(item['choices'])}。")
    if route_flips:
        for item in route_flips:
            lines.append(f"- 模型路由 `{item['id']}`：{', '.join(item['choices'])}。")
    if not context_flips and not path_flips and not route_flips:
        lines.append("三轮没有发现阈值决策或 Choice 翻转。")
    lines.extend(
        [
            "",
            "重复运行只验证相同输入下的稳定性，不覆盖模型升级、真实分布变化或候选集合扩张。",
            "",
        ]
    )
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

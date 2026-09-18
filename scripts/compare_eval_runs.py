#!/usr/bin/env python3
"""Compare repeated Jev runs and report decision and probability stability."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


BINARY_FIELDS = ("urgent", "needs_human", "missing_info")


def load_results(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return {result["id"]: result for result in data["results"] if "response" in result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if len(args.runs) < 2:
        parser.error("provide at least two run files")
    runs = [load_results(path) for path in args.runs]
    common_ids = sorted(set.intersection(*(set(run) for run in runs)))
    category_stable = 0
    binary_stable = {field: 0 for field in BINARY_FIELDS}
    binary_ranges = {field: [] for field in BINARY_FIELDS}
    frustration_ranges = []
    category_flips = []

    for case_id in common_ids:
        rows = [run[case_id] for run in runs]
        choices = [row["response"]["answers"]["category"]["choice"] for row in rows]
        if len(set(choices)) == 1:
            category_stable += 1
        else:
            category_flips.append({"id": case_id, "choices": choices})
        for field in BINARY_FIELDS:
            values = [float(row["response"]["answers"][field]["noul"]) for row in rows]
            binary_ranges[field].append(max(values) - min(values))
            if len({value >= 0.5 for value in values}) == 1:
                binary_stable[field] += 1
        scores = [float(row["response"]["answers"]["frustration"]["score"]) for row in rows]
        frustration_ranges.append(max(scores) - min(scores))

    count = len(common_ids)
    lines = [
        "# Jev 重复运行稳定性",
        "",
        f"> 比较运行数：{len(runs)}",
        f"> 共同样例数：{count}",
        "",
        "## 决策稳定性",
        "",
        f"- Category Choice 完全一致：{category_stable}/{count} ({category_stable / count:.1%})。",
    ]
    for field in BINARY_FIELDS:
        lines.append(
            f"- `{field}` 二值决策一致：{binary_stable[field]}/{count} "
            f"({binary_stable[field] / count:.1%})。"
        )
    lines.extend(["", "## 数值漂移", "", "| 输出 | 平均极差 | 最大极差 |", "| --- | ---: | ---: |"])
    for field in BINARY_FIELDS:
        lines.append(
            f"| `{field}` Noul | {statistics.fmean(binary_ranges[field]):.4f} | "
            f"{max(binary_ranges[field]):.4f} |"
        )
    lines.append(
        f"| `frustration` Score | {statistics.fmean(frustration_ranges):.4f} | "
        f"{max(frustration_ranges):.4f} |"
    )
    lines.extend(["", "## Category 翻转", ""])
    if category_flips:
        for item in category_flips:
            lines.append(f"- `{item['id']}`：{', '.join(item['choices'])}")
    else:
        lines.append("没有发现 Category Choice 翻转。")
    lines.extend(
        [
            "",
            "## 限制",
            "",
            "重复运行只衡量同一输入的稳定性，不衡量输入改写、真实分布变化或模型版本升级后的稳定性。",
            "",
        ]
    )
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Evaluate Jev for context filtering, semantic pathfinding, and model routing."""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

try:
    from scripts.evaluate_support import load_dotenv_key, request_evaluation
except ModuleNotFoundError:
    from evaluate_support import load_dotenv_key, request_evaluation


ROUTES = {
    "small_local": "A small local model or deterministic code is sufficient; the task is narrow and low-risk.",
    "fast_general": "A fast general coding model is appropriate; the task is bounded but needs normal implementation judgment.",
    "strong_reasoning": "Use the strongest reasoning model; the task is ambiguous, cross-system, high-risk, or requires deep diagnosis.",
}
ROUTE_COST = {"small_local": 1, "fast_general": 4, "strong_reasoning": 20}
TOKEN_RE = re.compile(r"[a-z0-9]+")


def load_dataset(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("context_filtering", "semantic_pathfinding", "model_routing"):
        if not isinstance(data.get(key), list) or not data[key]:
            raise ValueError(f"dataset requires a non-empty {key} list")
    return data


def choice(answer: Mapping[str, Any]) -> str:
    value = answer.get("choice")
    if not isinstance(value, str):
        raise ValueError("choice answer is missing choice")
    return value


def binary_metrics(expected: Sequence[bool], predicted: Sequence[bool]) -> Dict[str, float]:
    tp = sum(e and p for e, p in zip(expected, predicted))
    fp = sum(not e and p for e, p in zip(expected, predicted))
    fn = sum(e and not p for e, p in zip(expected, predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = sum(e == p for e, p in zip(expected, predicted)) / len(expected)
    return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}


def context_metrics(cases: Sequence[Mapping[str, Any]], decisions: Mapping[str, Mapping[str, bool]]) -> Dict[str, Any]:
    expected: list[bool] = []
    predicted: list[bool] = []
    kept_chars = 0
    total_chars = 0
    oracle_kept_chars = 0
    unsafe_drops = []
    for case in cases:
        case_decisions = decisions[case["id"]]
        for artifact in case["artifacts"]:
            want = bool(artifact["keep"])
            got = bool(case_decisions[artifact["id"]])
            expected.append(want)
            predicted.append(got)
            total_chars += int(artifact["chars"])
            if want:
                oracle_kept_chars += int(artifact["chars"])
            if got:
                kept_chars += int(artifact["chars"])
            if want and not got:
                unsafe_drops.append(f"{case['id']}:{artifact['id']}")
    metrics = binary_metrics(expected, predicted)
    metrics.update(
        {
            "artifacts": len(expected),
            "reduction_ratio": (total_chars - kept_chars) / total_chars if total_chars else 0.0,
            "oracle_reduction_ratio": (
                (total_chars - oracle_kept_chars) / total_chars if total_chars else 0.0
            ),
            "unsafe_drops": unsafe_drops,
        }
    )
    return metrics


def recent_baseline(cases: Sequence[Mapping[str, Any]], keep_count: int = 2) -> Dict[str, Dict[str, bool]]:
    output = {}
    for case in cases:
        ordered = sorted(case["artifacts"], key=lambda item: int(item["age"]))
        kept = {item["id"] for item in ordered[:keep_count]}
        output[case["id"]] = {item["id"]: item["id"] in kept for item in case["artifacts"]}
    return output


def lexical_path(query: str, candidates: Sequence[str]) -> str:
    query_tokens = set(TOKEN_RE.findall(query.lower()))
    scored = []
    for index, path in enumerate(candidates):
        path_tokens = set(TOKEN_RE.findall(path.lower().replace("_", " ")))
        scored.append((len(query_tokens & path_tokens), -index, path))
    return max(scored)[2]


def route_baseline(task: str) -> str:
    text = task.lower()
    strong_terms = (
        "distributed", "redesign", "zero-downtime", "multiple regions", "corruption",
        "cross services", "permission model", "replay attacks", "deadlock",
    )
    small_terms = ("rename a local", "extract all", "sort the keys", "doc comments", "pure string")
    if any(term in text for term in strong_terms):
        return "strong_reasoning"
    if any(term in text for term in small_terms):
        return "small_local"
    return "fast_general"


def route_metrics(cases: Sequence[Mapping[str, Any]], selected: Mapping[str, str]) -> Dict[str, Any]:
    correct = 0
    under = 0
    over = 0
    selected_cost = 0
    oracle_cost = 0
    order = {"small_local": 0, "fast_general": 1, "strong_reasoning": 2}
    errors = []
    for case in cases:
        expected = case["route"]
        actual = selected[case["id"]]
        correct += actual == expected
        under += order[actual] < order[expected]
        over += order[actual] > order[expected]
        selected_cost += ROUTE_COST[actual]
        oracle_cost += ROUTE_COST[expected]
        if actual != expected:
            errors.append({"id": case["id"], "expected": expected, "selected": actual})
    return {
        "accuracy": correct / len(cases),
        "under_route_rate": under / len(cases),
        "over_route_rate": over / len(cases),
        "relative_cost": selected_cost / oracle_cost,
        "errors": errors,
    }


def mean_latency(rows: Iterable[Mapping[str, Any]]) -> float:
    values = [float(row["latency_ms"]) for row in rows]
    return statistics.fmean(values) if values else 0.0


def evaluate_context(cases, api_key, model, timeout, max_attempts):
    rows = []
    decisions: Dict[str, Dict[str, bool]] = {}
    for case in cases:
        print(f"context {case['id']}", flush=True)
        state = {
            "task": case["goal"],
            "conversation_status": case["history"],
            "artifacts": [
                {key: artifact[key] for key in ("id", "age", "kind", "source", "content", "chars")}
                for artifact in case["artifacts"]
            ],
        }
        questions = {
            f"keep_{artifact['id']}": {
                "type": "noul",
                "instructions": (
                    f"Should artifact {artifact['id']} remain in the active context because its exact evidence "
                    "is still useful for completing the current task? Keep constraints, unresolved failures, "
                    "current implementation evidence, and facts needed for verification. Drop superseded, "
                    "unrelated, or reproducible low-value output."
                ),
            }
            for artifact in case["artifacts"]
        }
        result = request_evaluation(api_key, state, questions, model, timeout, max_attempts)
        answers = result["response"]["answers"]
        decisions[case["id"]] = {
            artifact["id"]: float(answers[f"keep_{artifact['id']}"]["noul"]) >= 0.5
            for artifact in case["artifacts"]
        }
        rows.append({"id": case["id"], **result})
        time.sleep(0.1)
    return {
        "rows": rows,
        "decisions": decisions,
        "metrics": context_metrics(cases, decisions),
        "recent_two_baseline": context_metrics(cases, recent_baseline(cases, 2)),
    }


def evaluate_pathfinding(cases, api_key, model, timeout, max_attempts):
    rows = []
    predicted = {}
    lexical = {}
    for case in cases:
        print(f"path {case['id']}", flush=True)
        candidate_map = {f"p{index + 1}": path for index, path in enumerate(case["candidates"])}
        result = request_evaluation(
            api_key,
            {"task": case["query"], "candidate_paths": candidate_map},
            {
                "path": {
                    "type": "choice",
                    "instructions": "Choose the single most likely code path to inspect first for this task.",
                    "criteria": {key: value for key, value in candidate_map.items()},
                }
            },
            model,
            timeout,
            max_attempts,
        )
        selected_key = choice(result["response"]["answers"]["path"])
        predicted[case["id"]] = candidate_map[selected_key]
        lexical[case["id"]] = lexical_path(case["query"], case["candidates"])
        rows.append({"id": case["id"], "selected": predicted[case["id"]], **result})
        time.sleep(0.1)

    def score(values):
        errors = [
            {"id": case["id"], "expected": case["target"], "selected": values[case["id"]]}
            for case in cases if values[case["id"]] != case["target"]
        ]
        return {"top1_accuracy": 1 - len(errors) / len(cases), "errors": errors}

    return {"rows": rows, "metrics": score(predicted), "lexical_baseline": score(lexical)}


def evaluate_routing(cases, api_key, model, timeout, max_attempts):
    rows = []
    selected = {}
    for case in cases:
        print(f"route {case['id']}", flush=True)
        result = request_evaluation(
            api_key,
            {"coding_task": case["task"]},
            {
                "route": {
                    "type": "choice",
                    "instructions": (
                        "Choose the least expensive route that is still likely to complete the task correctly. "
                        "Treat security, irreversible changes, distributed failures, and ambiguous cross-system "
                        "work conservatively."
                    ),
                    "criteria": ROUTES,
                }
            },
            model,
            timeout,
            max_attempts,
        )
        selected[case["id"]] = choice(result["response"]["answers"]["route"])
        rows.append({"id": case["id"], "selected": selected[case["id"]], **result})
        time.sleep(0.1)
    baseline = {case["id"]: route_baseline(case["task"]) for case in cases}
    all_strong = {case["id"]: "strong_reasoning" for case in cases}
    return {
        "rows": rows,
        "metrics": route_metrics(cases, selected),
        "keyword_baseline": route_metrics(cases, baseline),
        "all_strong_baseline": route_metrics(cases, all_strong),
    }


def render_report(run: Mapping[str, Any]) -> str:
    context = run["context_filtering"]
    path = run["semantic_pathfinding"]
    routing = run["model_routing"]
    return f"""# Jev Agent 控制面三项验证

> 日期：2026 年 9 月 18 日  
> 模型：`{run['requested_model']}`  
> 范围：合成小样本，用于发现方向性信号，不是生产 benchmark。

## 结论摘要

- 上下文过滤：关键内容召回率 **{context['metrics']['recall']:.1%}**，字符压缩率 **{context['metrics']['reduction_ratio']:.1%}**，危险误删 {len(context['metrics']['unsafe_drops'])} 项。
- 语义寻路：Jev Top-1 **{path['metrics']['top1_accuracy']:.1%}**，词法重叠基线 **{path['lexical_baseline']['top1_accuracy']:.1%}**。
- 模型路由：Jev 路由准确率 **{routing['metrics']['accuracy']:.1%}**，错误降级率 **{routing['metrics']['under_route_rate']:.1%}**，相对 oracle 成本 **{routing['metrics']['relative_cost']:.2f}x**。

## 1. 上下文过滤

| 方法 | Keep Precision | 关键召回率 | F1 | 字符压缩率 | 危险误删 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Jev | {context['metrics']['precision']:.1%} | {context['metrics']['recall']:.1%} | {context['metrics']['f1']:.3f} | {context['metrics']['reduction_ratio']:.1%} | {len(context['metrics']['unsafe_drops'])} |
| 只保留最近 2 项 | {context['recent_two_baseline']['precision']:.1%} | {context['recent_two_baseline']['recall']:.1%} | {context['recent_two_baseline']['f1']:.3f} | {context['recent_two_baseline']['reduction_ratio']:.1%} | {len(context['recent_two_baseline']['unsafe_drops'])} |

这组标签下的理论最大安全压缩率只有 {context['metrics']['oracle_reduction_ratio']:.1%}，因为三个仍需保留的截图占据了大部分字符；Jev 已取得其中绝大多数可删除空间。平均端到端延迟为 {mean_latency(context['rows']):.0f} ms。该测试让模型看到工具结果的短内容；它比只提供“结果长度”的 Fast Jev Compaction 条件更有利。生产使用仍应采用可恢复存根，并把用户约束、未解决错误和待验证修改设为确定性保留项。

危险误删：{', '.join(context['metrics']['unsafe_drops']) or '无'}。

## 2. 语义寻路

| 方法 | Top-1 Accuracy | 错误数 |
| --- | ---: | ---: |
| Jev | {path['metrics']['top1_accuracy']:.1%} | {len(path['metrics']['errors'])} |
| 词法重叠 | {path['lexical_baseline']['top1_accuracy']:.1%} | {len(path['lexical_baseline']['errors'])} |

Jev 平均端到端延迟为 {mean_latency(path['rows']):.0f} ms。这里仅验证“从少量候选路径中选第一跳”，尚未验证大型代码库中的多轮 walker、召回率和总搜索成本。

## 3. 模型路由

| 方法 | 路由准确率 | 错误降级 | 过度升级 | 相对 oracle 成本 |
| --- | ---: | ---: | ---: | ---: |
| Jev | {routing['metrics']['accuracy']:.1%} | {routing['metrics']['under_route_rate']:.1%} | {routing['metrics']['over_route_rate']:.1%} | {routing['metrics']['relative_cost']:.2f}x |
| 关键词规则 | {routing['keyword_baseline']['accuracy']:.1%} | {routing['keyword_baseline']['under_route_rate']:.1%} | {routing['keyword_baseline']['over_route_rate']:.1%} | {routing['keyword_baseline']['relative_cost']:.2f}x |
| 全部强模型 | {routing['all_strong_baseline']['accuracy']:.1%} | {routing['all_strong_baseline']['under_route_rate']:.1%} | {routing['all_strong_baseline']['over_route_rate']:.1%} | {routing['all_strong_baseline']['relative_cost']:.2f}x |

Jev 平均端到端延迟为 {mean_latency(routing['rows']):.0f} ms。这里的“正确路由”是人工定义的最低够用等级，尚未实际调用下游模型完成任务，因此只能验证难度判断，不能直接证明真实成本下降或成功率不变。

## 限制

- 三组数据均为人工合成，样本量分别为 {len(context['rows'])}、{len(path['rows'])} 和 {len(routing['rows'])}。
- 规则基线在看到数据设计后编写，只用于检查任务是否过于简单。
- 单轮报告不单独体现重复运行结果；稳定性见跨运行比较报告。长上下文、真实仓库规模和下游模型实际成功率仍未验证。
- 下一步应使用本项目真实历史、盲标任务以及实际小模型/强模型执行结果复验。
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("evals/agent-control-v1.json"))
    parser.add_argument("--model", default="jev-1.13.0")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/agent-control-v1-2026-09-18.json"))
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--max-attempts", type=int, default=4)
    args = parser.parse_args()

    load_dotenv_key(args.env_file)
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        parser.error("TYPESAFE_API_KEY is not set")
    data = load_dataset(args.dataset)
    started = datetime.now(timezone.utc).isoformat()
    run = {
        "dataset": str(args.dataset),
        "requested_model": args.model,
        "started_at": started,
        "context_filtering": evaluate_context(data["context_filtering"], api_key, args.model, args.timeout, args.max_attempts),
        "semantic_pathfinding": evaluate_pathfinding(data["semantic_pathfinding"], api_key, args.model, args.timeout, args.max_attempts),
        "model_routing": evaluate_routing(data["model_routing"], api_key, args.model, args.timeout, args.max_attempts),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = args.output.with_suffix(".md")
    report.write_text(render_report(run), encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Wrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

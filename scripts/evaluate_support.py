#!/usr/bin/env python3
"""Run and score the support-routing Jev benchmark without third-party packages."""

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
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence


API_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
RETRYABLE_STATUS = {429, 500, 502, 503, 504, 529}
BINARY_FIELDS = ("urgent", "needs_human", "missing_info")


def load_dotenv_key(path: Path) -> None:
    """Load only TYPESAFE_API_KEY without logging or exposing the value."""
    if os.environ.get("TYPESAFE_API_KEY") or not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != "TYPESAFE_API_KEY":
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if value:
            os.environ["TYPESAFE_API_KEY"] = value
        return


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            cases.append(item)
    return cases


def validate_cases(cases: Sequence[Mapping[str, Any]], categories: Iterable[str]) -> None:
    category_set = set(categories)
    seen_ids = set()
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("every case needs a non-empty string id")
        if case_id in seen_ids:
            raise ValueError(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)
        if not isinstance(case.get("state"), str) or not case["state"].strip():
            raise ValueError(f"{case_id}: state must be a non-empty string")
        expected = case.get("expected")
        if not isinstance(expected, Mapping):
            raise ValueError(f"{case_id}: expected must be an object")
        if expected.get("category") not in category_set:
            raise ValueError(f"{case_id}: unknown category {expected.get('category')!r}")
        for field in BINARY_FIELDS:
            if not isinstance(expected.get(field), bool):
                raise ValueError(f"{case_id}: {field} must be boolean")
        frustration = expected.get("frustration")
        if isinstance(frustration, bool) or frustration not in {0, 1, 2}:
            raise ValueError(f"{case_id}: frustration must be 0, 1, or 2")


def percentile(values: Sequence[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percentile_value
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def macro_f1(expected: Sequence[str], predicted: Sequence[str], labels: Sequence[str]) -> float:
    scores = []
    for label in labels:
        true_positive = sum(e == label and p == label for e, p in zip(expected, predicted))
        false_positive = sum(e != label and p == label for e, p in zip(expected, predicted))
        false_negative = sum(e == label and p != label for e, p in zip(expected, predicted))
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        score = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores.append(score)
    return statistics.fmean(scores) if scores else 0.0


def expected_calibration_error(confidences: Sequence[float], correct: Sequence[bool], bins: int = 10) -> float:
    if not confidences:
        return 0.0
    total = len(confidences)
    error = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        members = [
            item
            for item, confidence in enumerate(confidences)
            if lower <= confidence < upper or (index == bins - 1 and confidence == 1.0)
        ]
        if not members:
            continue
        average_confidence = statistics.fmean(confidences[item] for item in members)
        accuracy = statistics.fmean(1.0 if correct[item] else 0.0 for item in members)
        error += len(members) / total * abs(accuracy - average_confidence)
    return error


def coverage_accuracy(
    confidences: Sequence[float], correct: Sequence[bool], thresholds: Sequence[float]
) -> Dict[str, Dict[str, float]]:
    output: Dict[str, Dict[str, float]] = {}
    for threshold in thresholds:
        members = [index for index, confidence in enumerate(confidences) if confidence >= threshold]
        output[f"{threshold:.2f}"] = {
            "coverage": len(members) / len(confidences) if confidences else 0.0,
            "accuracy": (
                statistics.fmean(1.0 if correct[index] else 0.0 for index in members)
                if members
                else 0.0
            ),
            "count": len(members),
        }
    return output


def validate_response(response: Mapping[str, Any], question_ids: Iterable[str]) -> None:
    answers = response.get("answers")
    if not isinstance(answers, Mapping):
        raise ValueError("response does not contain an answers object")
    missing = set(question_ids) - set(answers)
    if missing:
        raise ValueError(f"response omitted answers: {', '.join(sorted(missing))}")

    for question_id in question_ids:
        answer = answers[question_id]
        answer_type = answer.get("type")
        if answer_type == "noul":
            value = answer.get("noul")
            if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{question_id} is not a valid Noul probability")
            continue
        if answer_type not in {"choice", "score"}:
            raise ValueError(f"{question_id} has unknown answer type {answer_type!r}")
        probabilities = answer.get("probabilities")
        if not isinstance(probabilities, Mapping) or not probabilities:
            raise ValueError(f"{question_id} probabilities are missing")
        numbers = list(probabilities.values())
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in numbers):
            raise ValueError(f"{question_id} probabilities contain invalid values")
        if abs(sum(numbers) - 1.0) > 0.02:
            raise ValueError(f"{question_id} probabilities do not sum to one")


def request_evaluation(
    api_key: str,
    state: str,
    questions: Mapping[str, Any],
    model: str,
    timeout: float,
    max_attempts: int,
) -> Dict[str, Any]:
    payload = json.dumps({"model": model, "state": state, "questions": questions}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "jev-lab-evaluation/1.0",
    }
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(API_URL, data=payload, headers=headers, method="POST")
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read().decode("utf-8")
            parsed = json.loads(body)
            validate_response(parsed, questions.keys())
            return {
                "response": parsed,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "attempts": attempt,
            }
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(f"HTTP {exc.code}: {body[:500]}")
            if exc.code not in RETRYABLE_STATUS or attempt == max_attempts:
                raise last_error from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            if attempt == max_attempts:
                raise
        delay = min(8.0, 2 ** (attempt - 1))
        time.sleep(delay)
    raise RuntimeError(f"request failed: {last_error}")


def calculate_metrics(results: Sequence[Mapping[str, Any]], category_labels: Sequence[str]) -> Dict[str, Any]:
    completed = [result for result in results if "response" in result]
    errors = [result for result in results if "error" in result]
    if not completed:
        return {"completed": 0, "errors": len(errors)}

    expected_categories: List[str] = []
    predicted_categories: List[str] = []
    category_correct: List[bool] = []
    category_top_probabilities: List[float] = []
    category_official_confidences: List[float] = []
    category_expected_probabilities: List[float] = []
    category_brier_values: List[float] = []
    category_nll_values: List[float] = []

    binary_values: Dict[str, MutableMapping[str, List[Any]]] = {
        field: {"probabilities": [], "expected": [], "correct": [], "decision_confidence": []}
        for field in BINARY_FIELDS
    }
    frustration_errors: List[float] = []
    frustration_correct: List[bool] = []
    frustration_brier_values: List[float] = []
    latencies: List[float] = []
    input_tokens = 0
    output_tokens = 0
    models = Counter()

    group_categories: Dict[str, List[str]] = defaultdict(list)
    group_binary: Dict[str, Dict[str, List[bool]]] = defaultdict(lambda: defaultdict(list))

    for result in completed:
        expected = result["expected"]
        response = result["response"]
        answers = response["answers"]
        category = answers["category"]
        probabilities = {label: float(category["probabilities"].get(label, 0.0)) for label in category_labels}
        expected_label = expected["category"]
        predicted_label = category["choice"]
        is_correct = predicted_label == expected_label

        expected_categories.append(expected_label)
        predicted_categories.append(predicted_label)
        category_correct.append(is_correct)
        category_top_probabilities.append(max(probabilities.values()))
        category_official_confidences.append(float(category.get("confidence", 0.0)))
        expected_probability = probabilities[expected_label]
        category_expected_probabilities.append(expected_probability)
        category_brier_values.append(
            sum((probabilities[label] - (1.0 if label == expected_label else 0.0)) ** 2 for label in category_labels)
        )
        category_nll_values.append(-math.log(max(expected_probability, 1e-12)))
        group_categories[result["group"]].append(predicted_label)

        for field in BINARY_FIELDS:
            probability = float(answers[field]["noul"])
            expected_value = bool(expected[field])
            predicted_value = probability >= 0.5
            correct = predicted_value == expected_value
            binary_values[field]["probabilities"].append(probability)
            binary_values[field]["expected"].append(expected_value)
            binary_values[field]["correct"].append(correct)
            binary_values[field]["decision_confidence"].append(max(probability, 1 - probability))
            group_binary[result["group"]][field].append(predicted_value)

        score_answer = answers["frustration"]
        predicted_score = float(score_answer["score"])
        expected_score = int(expected["frustration"])
        frustration_errors.append(abs(predicted_score - expected_score))
        frustration_correct.append(round(predicted_score) == expected_score)
        score_probabilities = {
            index: float(score_answer.get("probabilities", {}).get(str(index), 0.0)) for index in range(3)
        }
        frustration_brier_values.append(
            sum((score_probabilities[index] - (1.0 if index == expected_score else 0.0)) ** 2 for index in range(3))
        )

        latencies.append(float(result["latency_ms"]))
        usage = response.get("usage", {})
        input_tokens += int(usage.get("input_tokens", 0))
        output_tokens += int(usage.get("output_tokens", 0))
        models[str(response.get("model", "unknown"))] += 1

    binary_summary = {}
    for field, values in binary_values.items():
        probabilities = values["probabilities"]
        expected_values = values["expected"]
        correct = values["correct"]
        decision_confidences = values["decision_confidence"]
        binary_summary[field] = {
            "accuracy": statistics.fmean(1.0 if item else 0.0 for item in correct),
            "brier": statistics.fmean(
                (probability - (1.0 if expected_value else 0.0)) ** 2
                for probability, expected_value in zip(probabilities, expected_values)
            ),
            "ece": expected_calibration_error(decision_confidences, correct),
            "coverage_accuracy": coverage_accuracy(decision_confidences, correct, (0.6, 0.75, 0.9)),
        }

    category_group_consistency = statistics.fmean(
        1.0 if len(set(predictions)) == 1 else 0.0 for predictions in group_categories.values()
    )
    binary_group_consistency = {
        field: statistics.fmean(
            1.0 if len(set(field_values[field])) == 1 else 0.0 for field_values in group_binary.values()
        )
        for field in BINARY_FIELDS
    }

    return {
        "completed": len(completed),
        "errors": len(errors),
        "models": dict(models),
        "category": {
            "accuracy": statistics.fmean(1.0 if item else 0.0 for item in category_correct),
            "macro_f1": macro_f1(expected_categories, predicted_categories, list(category_labels)),
            "mean_expected_probability": statistics.fmean(category_expected_probabilities),
            "multiclass_brier": statistics.fmean(category_brier_values),
            "negative_log_likelihood": statistics.fmean(category_nll_values),
            "top_probability_ece": expected_calibration_error(category_top_probabilities, category_correct),
            "official_confidence_coverage": coverage_accuracy(
                category_official_confidences, category_correct, (0.5, 0.7, 0.85)
            ),
            "group_consistency": category_group_consistency,
        },
        "binary": binary_summary,
        "frustration": {
            "mean_absolute_error": statistics.fmean(frustration_errors),
            "rounded_accuracy": statistics.fmean(1.0 if item else 0.0 for item in frustration_correct),
            "multiclass_brier": statistics.fmean(frustration_brier_values),
        },
        "robustness": {
            "category_group_consistency": category_group_consistency,
            "binary_group_consistency": binary_group_consistency,
        },
        "latency_ms": {
            "mean": statistics.fmean(latencies),
            "p50": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
            "max": max(latencies),
        },
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


def percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_report(run: Mapping[str, Any]) -> str:
    metrics = run["metrics"]
    category = metrics["category"]
    title = "关键词基线结果" if run["requested_model"].startswith("keyword-") else "Jev 客服路由基准结果"
    lines = [
        f"# {title}",
        "",
        f"> 运行时间：{run['finished_at']}",
        f"> 数据集：`{run['dataset']}`",
        f"> 请求模型：`{run['requested_model']}`",
        f"> 实际模型：`{', '.join(metrics['models'])}`",
        "",
        "## 摘要",
        "",
        f"- 完成 {metrics['completed']} 条，错误 {metrics['errors']} 条。",
        f"- 类别准确率：{percentage(category['accuracy'])}。",
        f"- 类别 Macro F1：{category['macro_f1']:.3f}。",
        f"- 类别改写组一致率：{percentage(category['group_consistency'])}。",
        f"- 类别 Brier：{category['multiclass_brier']:.3f}，NLL：{category['negative_log_likelihood']:.3f}。",
        f"- 延迟 P50/P95：{metrics['latency_ms']['p50']:.0f} ms / {metrics['latency_ms']['p95']:.0f} ms。",
        f"- Token 用量：输入 {metrics['usage']['input_tokens']}，输出 {metrics['usage']['output_tokens']}。",
        "",
        "## 各判断指标",
        "",
        "| 判断 | Accuracy | Brier | ECE | 改写组一致率 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for field in BINARY_FIELDS:
        item = metrics["binary"][field]
        consistency = metrics["robustness"]["binary_group_consistency"][field]
        lines.append(
            f"| `{field}` | {percentage(item['accuracy'])} | {item['brier']:.3f} | "
            f"{item['ece']:.3f} | {percentage(consistency)} |"
        )
    lines.extend(
        [
            "",
            "## 情绪评分",
            "",
            f"- MAE：{metrics['frustration']['mean_absolute_error']:.3f}。",
            f"- 四舍五入准确率：{percentage(metrics['frustration']['rounded_accuracy'])}。",
            f"- Multiclass Brier：{metrics['frustration']['multiclass_brier']:.3f}。",
            "",
            "## 类别置信度门控",
            "",
            "官方 `confidence` 是概率分布集中程度，不等同于答对概率。下表只用于观察门控效果。",
            "",
            "| 阈值 | 覆盖率 | 覆盖样本准确率 | 样本数 |",
            "| ---: | ---: | ---: | ---: |",
        ]
    )
    for threshold, item in category["official_confidence_coverage"].items():
        lines.append(
            f"| {threshold} | {percentage(item['coverage'])} | {percentage(item['accuracy'])} | {item['count']} |"
        )
    lines.extend(
        [
            "",
            "## 解释限制",
            "",
            "- 这是人工构造的小规模基准，不代表真实生产分布。",
            "- 标签由当前项目定义，尤其是 `needs_human` 和情绪等级包含业务判断。",
            "- 同组改写共享标签，适合测稳定性，但不能替代独立真实工单测试集。",
            "- 在加入开源小模型、传统分类器和通用 LLM 基线前，不能据此判断 Jev 的相对价值。",
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
    parser.add_argument("--cases", type=Path, default=Path("evals/support-routing-v1.jsonl"))
    parser.add_argument("--questions", type=Path, default=Path("evals/support-routing-v1.questions.json"))
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--run-name", default=datetime.now(timezone.utc).strftime("support-routing-v1-%Y%m%dT%H%M%SZ"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--max-attempts", type=int, default=4)
    parser.add_argument("--sleep", type=float, default=0.15)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    questions = load_json(args.questions)
    cases = load_jsonl(args.cases)
    if args.limit is not None:
        cases = cases[: args.limit]
    category_labels = list(questions["category"]["criteria"])
    validate_cases(cases, category_labels)
    if args.validate_only:
        print(f"Validated {len(cases)} cases and {len(questions)} questions.")
        return 0

    load_dotenv_key(args.env_file)
    api_key = os.environ.get("TYPESAFE_API_KEY")
    if not api_key:
        print("TYPESAFE_API_KEY is not set.", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / f"{args.run_name}.json"
    report_path = args.output_dir / f"{args.run_name}.md"

    results: List[Dict[str, Any]] = []
    if args.resume and json_path.exists():
        previous = load_json(json_path)
        results = list(previous.get("results", []))
    completed_ids = {result["id"] for result in results}

    run: Dict[str, Any] = {
        "dataset": str(args.cases),
        "questions": str(args.questions),
        "requested_model": args.model,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }

    total = len(cases)
    for index, case in enumerate(cases, start=1):
        if case["id"] in completed_ids:
            continue
        print(f"[{index}/{total}] {case['id']}", flush=True)
        record: Dict[str, Any] = {
            "id": case["id"],
            "group": case.get("group", case["id"]),
            "state": case["state"],
            "expected": case["expected"],
        }
        try:
            evaluation = request_evaluation(
                api_key=api_key,
                state=case["state"],
                questions=questions,
                model=args.model,
                timeout=args.timeout,
                max_attempts=args.max_attempts,
            )
            record.update(evaluation)
        except Exception as exc:  # Keep the failure observable in the artifact and console.
            record["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  ERROR: {record['error']}", file=sys.stderr, flush=True)
        results.append(record)
        run["results"] = results
        checkpoint(json_path, run)
        if args.sleep > 0:
            time.sleep(args.sleep)

    run["finished_at"] = datetime.now(timezone.utc).isoformat()
    run["metrics"] = calculate_metrics(results, category_labels)
    checkpoint(json_path, run)
    report_path.write_text(render_report(run), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {report_path}")
    return 1 if run["metrics"].get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())

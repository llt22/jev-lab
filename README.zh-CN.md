# Jev Lab：TypeSafe System One 模型实测与基准

> 一个面向 [Jev](https://typesafe.ai) 的独立实验仓库：用可复现数据测试 Noul、Choice、Score 等结构化判断能力，覆盖客服路由、Agent 控制、置信度闸门与多问题 fan-out，并持续核验官方和社区说法。

[English](README.md) | **简体中文**

[![Tests](https://img.shields.io/badge/tests-38%20passed-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Model](https://img.shields.io/badge/model-jev--1.13.0-blueviolet)](https://docs.typesafe.ai/models)
[![Zero deps](https://img.shields.io/badge/deps-stdlib%20only-orange)](scripts/)

## 先看结论

Jev 是一个 **System One 模型**：输入 `state` 和带类型的问题，输出带概率的结构化答案，而不是生成文本。Noul 用于二元判断，Choice 用于多选一，Score 用于有序评分。

| 结论 | 实测结果 | 证据 |
| --- | --- | --- |
| Pilot 中 fan-out 延迟基本不变 | 1 → 20 个 Noul 问题，P50 均约 **1.4 秒** | [首轮验证](docs/jev-validation-2026-09-18.md) |
| 调用成本低 | 108 次请求合计约 **0.0044 美元** | [首轮验证](docs/jev-validation-2026-09-18.md) |
| 相同数据上的决策稳定 | 3 轮 × 36 条工单，决策一致率 **100%** | [原始产物](artifacts/) |
| 闸门应看 `confidence`，不能只看 top-1 概率 | 失败样本中 confidence 为 0.04–0.16，而 top-1 概率仍可达 0.58 | [第三轮调研](docs/jev-round3-2026-09-18.md) |
| 简单关键词基线胜过 Jev | 97.2% vs 91.7%，说明 pilot 数据太简单，不能把单次结果当生产准确率 | [首轮验证](docs/jev-validation-2026-09-18.md) |
| 完整链路延迟约 1.5 秒 | 与官方模型侧低延迟口径不同，当前数据包含网络与网关开销 | [首轮验证](docs/jev-validation-2026-09-18.md) |

核心提醒：概率不等于生产准确率。请在自己的数据上校准、固定模型版本，并把接近 0.5 的单个 Noul 判断视为“不确定”，而不是直接当成“否”。

## 快速开始

复制环境变量模板并填入 TypeSafe API Key：

```sh
cp .env.example .env
```

直接调用 API（需要 `curl`）：

```sh
set -a; . ./.env; set +a
curl --fail-with-body --silent --show-error \
  https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"jev-latest","state":"The customer cannot connect to Wi-Fi before a meeting today.","questions":{"urgent":{"type":"noul","instructions":"Does this message express urgency?"}}}'
```

离线运行全部单元测试，不需要 API Key 或第三方依赖：

```sh
python3 -m unittest discover -s tests
```

## 仓库内容

```text
docs/       5 轮共 8 份报告：验证、生态调研、官方说法核验、社区案例
evals/      6 组数据：客服路由、Agent 控制、置信度升级、思考监督
scripts/    9 个可复现的评测与对比脚本，仅使用 Python 标准库
artifacts/  原始 JSON 与生成报告，包括多轮重复稳定性结果
tests/      38 个可离线运行的单元测试
```

## 重点报告

| 报告 | 内容 |
| --- | --- |
| [首轮验证](docs/jev-validation-2026-09-18.md) | 客服工单路由、fan-out 延迟、成本、重复稳定性、关键词基线与 Agent 控制 |
| [思考监督实验](docs/jev-thinking-supervision-2026-09-18.md) | 通过第三方网关观察并尝试打断推理窗口；实验没有缩短最终回答 |
| [第三轮调研](docs/jev-round3-2026-09-18.md) | 官方说法核验、生态索引质量、置信度升级闸门 |
| [第四轮调研](docs/jev-round4-2026-09-19.md) | 第三方 benchmark、媒体报道、开源 System One 模型与生态风险 |
| [第四轮补充](docs/jev-round4-supplement-2026-09-19.md) | 官方文档变化、融资、平台集成、上下文压缩争议 |
| [第五轮调研](docs/jev-round5-2026-09-19.md) | 医疗、DevOps、ERP、内容评分、PR 与语音控制等真实使用案例 |
| [第五轮补充](docs/jev-round5-supplement-2026-09-19.md) | 28 个社区案例逐条核验与遗漏案例补录 |
| [社区用例调查](docs/jev-x-use-cases-2026-09-18.md) | X / GitHub 用法索引、风险与选型标准 |

## 复现实验

```sh
# 客服路由 benchmark 与关键词基线
python3 scripts/evaluate_support.py --run-name support-routing-v1
python3 scripts/evaluate_keyword_baseline.py

# 1 → 20 个并行问题的 fan-out 延迟
python3 scripts/benchmark_fanout.py

# 置信度升级闸门
python3 scripts/evaluate_confidence_escalation.py
```

需要 API 的脚本会明确检查 `TYPESAFE_API_KEY`；比较脚本和单元测试可离线运行。

## 参与项目

欢迎提交独立复现、反例、新数据集和文档纠错。请先阅读 [贡献指南](CONTRIBUTING.md)，也可以直接通过 [Benchmark 结果表单](https://github.com/llt22/jev-lab/issues/new?template=benchmark-result.yml) 分享结果，无需修改代码。

## 使用说明

本仓库是独立研究材料，不应把单轮概率当成生产准确率或自动执行权限。API 价格和模型版本以报告记录日期（2026-09-19）的官方文档为准；每份报告会区分已核验结构、厂商陈述和作者陈述。

仓库目前尚未声明开源许可证；在许可证加入前，默认版权限制仍然适用。

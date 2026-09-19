# Awesome Jev Lab

> 精选整理 **Jev / TypeSafe System One** 的官方资源、真实用例与可复现 benchmark。

**独立社区项目，与 TypeSafe 无隶属或背书关系。**

[English](README.md) | **简体中文**

[![Tests](https://img.shields.io/badge/tests-38%20passed-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Model](https://img.shields.io/badge/tested-jev--1.13.0-blueviolet)](https://docs.typesafe.ai/models)
[![Zero deps](https://img.shields.io/badge/lab-stdlib%20only-orange)](scripts/)

Jev 把自然语言状态转换成带类型的决策：**Noul** 做是/否判断，**Choice** 从候选项中选择，**Score** 做有序评分。本仓库既是 Jev 生态导航，也是一个独立实验室，提供原始数据、负面结果和完整复现脚本。

## 目录

- [从这里开始](#从这里开始)
- [官方资源](#官方资源)
- [SDK 与集成](#sdk-与集成)
- [精选用例](#精选用例)
- [可复现实测](#可复现实测)
- [运行实验](#运行实验)
- [研究归档](#研究归档)
- [参与项目](#参与项目)

## 从这里开始

| 目标 | 推荐入口 |
| --- | --- |
| 5 分钟了解 Jev | [TypeSafe Quick Start](https://docs.typesafe.ai/introduction/quickstart) |
| 选择架构模式 | [官方 Patterns](https://docs.typesafe.ai/patterns) |
| 看社区正在做什么 | [精选用例](#精选用例) |
| 用独立数据核对宣传 | [Jev Lab 首轮验证](docs/jev-validation-2026-09-18.md) |
| 自己复现实验 | [运行实验](#运行实验) |

## 官方资源

- [TypeSafe 官网](https://typesafe.ai)：产品简介与访问入口。
- [官方文档](https://docs.typesafe.ai/)：概念、指南和 API Reference。
- [模型列表](https://docs.typesafe.ai/models)：别名、固定版本和价格。
- [架构模式](https://docs.typesafe.ai/patterns)：fan-out、置信度路由、组合评分和意图路由。
- [用例地图](https://docs.typesafe.ai/concepts/use-case-map)：官方任务形态与应用分类。
- [TypeSafe GitHub 组织](https://github.com/orgs/typesafe-ai/repositories)：官方 SDK、Skills 与 Adapter。GitHub 存在名称相近但无关的组织，引用时应核对完整组织名。

## SDK 与集成

| 项目 | 用途 | 来源 |
| --- | --- | --- |
| Python SDK | 官方 TypeSafe Python API 客户端 | [typesafe-ai/typesafe-sdk-python](https://github.com/typesafe-ai/typesafe-sdk-python) |
| JavaScript SDK | 官方 JavaScript / TypeScript API 客户端 | [typesafe-ai/typesafe-sdk-js](https://github.com/typesafe-ai/typesafe-sdk-js) |
| Agent Skills | 使用 System One API 构建 Agent 的官方 Skills | [typesafe-ai/skills](https://github.com/typesafe-ai/skills) |
| System One Adapter | 用其他 LLM API 实现 TypeSafe 客户端契约 | [typesafe-ai/system-one-adapter-python](https://github.com/typesafe-ai/system-one-adapter-python) |
| Vercel AI Gateway | 通过 AI SDK Evaluation API 使用 `typesafe-ai/jev` | [Vercel 公告](https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway) |
| LangChain | Python / JS 集成、模型路由和工具风险中间件 | [集成指南](https://blog.langchain.com/building-a-harness-with-jev/) |
| OpenRouter | 托管的 `typesafe-ai/jev` 访问渠道 | [模型页面](https://openrouter.ai/typesafe-ai/jev) |
| Cline Browser Harness | 依据结构化 DOM 观察选择浏览器动作 | [cline/plugins/jev-browser](https://github.com/cline/plugins/tree/main/plugins/jev-browser) |

## 精选用例

以下是有代表性的项目和一手报告，不代表本仓库为其背书。证据标签用于区分可检查的开源实现和作者自报结果；更完整的生态宽度和限制见 [28 案例审计](docs/jev-round5-supplement-2026-09-19.md)。

### Agent 与交互

- [Cline Jev Browser](https://github.com/cline/plugins/tree/main/plugins/jev-browser)：带步数上限和明确审查状态的浏览器动作选择。**开源实现。**
- [Jev Voice Browser](https://github.com/moritzkremb/jev-voice-browser)：在语音仍在输入时判断意图并选择浏览器目标。**开源 Demo。**
- [jev-experiments](https://github.com/dabit3/jev-experiments)：预测式 UI、路由和决策实验合集。**开源实验。**

### 搜索、筛选与路由

- [TypeSafe Screening MCP](https://github.com/masa-med-ai/typesafe-screening-mcp)：按临床问题和纳排标准筛选 PubMed 标题与摘要。**开源实现，有作者一手运行数据。**
- [ERP、知识库与邮件搜索](https://x.com/bigfarmer666/status/2101114327722008829)：多源并行检索，并用 Jev 重排和消歧。**作者自报生产使用。**
- [边缘 k3s 决策管道](https://x.com/maro_kt/status/2101130758635258226)：拆分确定性代码、类型化决策与通用 LLM 推理。**作者自报现场实验。**

### 质量闸门与实时控制

- [AI 内容评分](https://x.com/noahxops/status/2101135688217538790)：发布前为生成内容的不同变体评分。**作者自报实验。**
- [Sprite Fusion 实时关卡生成](https://www.spritefusion.com/blog/generating-game-level-in-real-time-with-jev)：从有限候选中选择下一段地形。**有时间数据的公开 Demo。**

### 更多目录

- [awesome-jev](https://github.com/ckaraca/awesome-jev)：覆盖更广的项目和集成清单。
- [outjev.lol](https://outjev.lol)：按产品、Demo、实验标注的社区项目目录。
- [Jev Lab 社区调查](docs/jev-x-use-cases-2026-09-18.md)：带来源核验、风险和选型标准的索引。

## 可复现实测

以下数字只来自本仓库的 pilot 数据集，是实测观察，不是生产承诺。

| 问题 | 结果 | 证据 |
| --- | --- | --- |
| 1 到 20 个问题的 fan-out 是否增加延迟？ | 未观察到增长，P50 均约 **1.4 秒** | [报告](docs/jev-validation-2026-09-18.md) / [原始数据](artifacts/fanout-jev-1.13.0-2026-09-18.json) |
| 108 次请求成本多少？ | 合计约 **0.0044 美元** | [验证报告](docs/jev-validation-2026-09-18.md) |
| 决策是否稳定？ | 3 轮 x 36 条客服样本，决策一致率 **100%** | [稳定性报告](artifacts/support-routing-v1-repeat-stability-2026-09-18.md) |
| Jev 是否胜过简单基线？ | 没有；简单 pilot 上关键词规则 **97.2% vs 91.7%** | [基线结果](artifacts/support-routing-v1-keyword-baseline.md) |
| 安全闸门只看 top-1 概率是否足够？ | 不够；失败样本 confidence 为 0.04-0.16，top-1 仍可达 0.58 | [置信度实验](docs/jev-round3-2026-09-18.md) |
| 完整链路是否符合低于 100ms 的宣传？ | 没有；本环境端到端约 **1.5 秒** | [验证报告](docs/jev-validation-2026-09-18.md) |

实践结论：

1. 阈值调好后固定版本化模型 ID，不要长期依赖会漂移的别名。
2. 闸门读取 API 返回的 `confidence`，不能只看答案的最大概率。
3. 接近 0.5 的概率表示不确定，不应自动解释为“否”。
4. 中文与中英混合任务单独测试；官方文档明确英语效果最好。
5. 保存原始输入、输出、错误和重试记录，保证结果可以审计。

## 运行实验

单元测试和对比脚本只使用 Python 标准库；调用 API 的 benchmark 需要 TypeSafe Key。

```sh
cp .env.example .env
python3 -m unittest discover -s tests

# 客服路由与确定性关键词基线
python3 scripts/evaluate_support.py --run-name support-routing-v1
python3 scripts/evaluate_keyword_baseline.py

# Fan-out 延迟与置信度升级闸门
python3 scripts/benchmark_fanout.py
python3 scripts/evaluate_confidence_escalation.py
```

仓库结构：

```text
docs/       带来源核验的报告与研究笔记
evals/      版本化 benchmark 数据集
scripts/    可复现评测与对比工具
artifacts/  原始 JSON 输出与生成报告
tests/      离线单元测试
```

## 研究归档

| 主题 | 报告 |
| --- | --- |
| Benchmark 与校准 | [首轮验证](docs/jev-validation-2026-09-18.md) · [置信度闸门](docs/jev-round3-2026-09-18.md) |
| Agent 控制与思考监督 | [思考监督](docs/jev-thinking-supervision-2026-09-18.md) · [生态交叉核验](docs/jev-round4-2026-09-19.md) |
| 官方说法与平台集成 | [官方与平台审计](docs/jev-round4-supplement-2026-09-19.md) |
| 社区采用 | [一手用例](docs/jev-round5-2026-09-19.md) · [28 案例审计](docs/jev-round5-supplement-2026-09-19.md) · [社区调查](docs/jev-x-use-cases-2026-09-18.md) |

## 参与项目

独立复现、反例和新数据集尤其有价值。请阅读[贡献指南](CONTRIBUTING.md)，也可以直接[推荐资源](https://github.com/llt22/jev-lab/issues/new?template=resource-suggestion.yml)或[提交 Benchmark 结果](https://github.com/llt22/jev-lab/issues/new?template=benchmark-result.yml)，无需修改代码。

本仓库是研究材料。不要把单轮概率当成生产准确率或自动执行权限；价格、版本和生态状态以每份报告的记录日期为准。

仓库目前尚未声明开源许可证；在许可证加入前，默认版权限制仍然适用。

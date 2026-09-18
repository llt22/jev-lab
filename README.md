# Jev API 测试工作区

这是一个独立的 TypeSafe **Jev（System One）API** 实验目录，用来测试 Noul、Choice、Score 等结构化判断能力，并评估业务场景（例如客服工单分流）。它不属于 `ekc-ai-rebuild` 项目；目前只有环境配置，没有测试程序或 SDK 依赖。

## 准备

1. 在本目录的 `.env` 中填写 `TYPESAFE_API_KEY=你的密钥`。不要把密钥写入脚本、提交到 Git 或贴到聊天中。
2. `.gitignore` 已忽略 `.env`；`.env.example` 只提供变量名模板。

## 直接调用 API

在本目录的终端执行（需安装 `curl`）：

```sh
set -a
. ./.env
set +a

curl --fail-with-body --silent --show-error \
  https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"jev-latest","state":"The customer cannot connect to Wi-Fi before a meeting today.","questions":{"urgent":{"type":"noul","instructions":"Does this message express urgency?"}}}'
```

成功时返回 `answers.urgent.noul`（0–1）以及实际模型版本和 token 用量。API 接口和更多问题类型见 [TypeSafe Quick Start](https://docs.typesafe.ai/introduction/quickstart) 与 [API Reference](https://docs.typesafe.ai/api)。

## 调研与实测记录

| 文档 | 内容 |
| --- | --- |
| [社区应用调研](docs/jev-x-use-cases-2026-09-18.md) | X / GitHub 上的用法、案例索引、风险与选型判断 |
| [首轮验证报告](docs/jev-validation-2026-09-18.md) | 客服路由基准、fan-out、成本、重复稳定性、关键词基线、Agent 控制面三项 |
| [流式思考监督](docs/jev-thinking-supervision-2026-09-18.md) | 通过第三方网关观察思考窗口并尝试打断（机制实验，未成功缩短作答） |
| [第三轮调研](docs/jev-round3-2026-09-18.md) | 官方口径核实、生态索引质量、置信度升级闸门三轮实测 |

原始产物在 `artifacts/`，数据集在 `evals/`，评测脚本在 `scripts/`，单元测试在 `tests/`。

## 接下来

在此目录加入可重复的真实业务样例，比较 Jev 对不同表述的路由、优先级和置信度；不要把单次概率直接当作生产准确率或自动执行权限。

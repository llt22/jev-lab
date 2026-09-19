# json-render 与 Jev 最小集成验证

> 日期：2026 年 9 月 19 日
>
> json-render：`@json-render/core@0.21.0`、`@json-render/react@0.21.0`
>
> 范围：官方组合与渲染链路的本地验证，以及 TypeSafe API 真实 Jev 请求

## 结论

官方实现可以工作，不只是概念代码。本实验复用了正式发布包中的
`experimental_composeSpec`，从应用提供的七个候选中完成两阶段选择：

1. `select` 批量选择 dashboard、订单表、指标行、三个指标和周收入图；
2. `layout` 把三个指标放入指标行，并按“订单表 → 指标行 → 周收入图”排列。

composer 生成的 flat Spec 通过 catalog 校验，随后由 `@json-render/react`
渲染为 HTML。离线回归使用确定性 evaluator 验证组合、校验和渲染；真实运行则通过
自定义 evaluator 直连 TypeSafe System One API，固定模型 `jev-1.13.0`。

## 实际结果

| 检查项 | 结果 |
| --- | --- |
| composer 完成原因 | `finish` |
| evaluation 批次 | 2（`select` + `layout`） |
| Spec 元素数 | 7 |
| catalog 校验 | 通过 |
| React HTML 渲染 | 通过 |
| 真实 Jev 端到端延迟 | 2,803 ms |
| 真实 Jev 输入 token | 3,395 |
| 真实 Jev 选择结果 | 7/7 候选正确，布局与顺序正确 |
| 结构、顺序与适配器测试 | 3/3 通过 |
| TypeScript 类型检查 | 通过 |

生成树为：

```text
Dashboard
├── OrdersTable
├── MetricRow
│   ├── Revenue
│   ├── Orders
│   └── New customers
└── RevenueBars
```

## 真实 Jev 观察

真实运行共两次 evaluation：`select` 约 1,970 ms，`layout` 约 830 ms。Jev
选择了全部七个所需候选，并把订单表、指标行、周收入图依次放入 dashboard，三个指标
依次放入指标行。详细的脱敏决策摘要见
[`artifacts/json-render-jev-1.13.0-2026-09-19.json`](../artifacts/json-render-jev-1.13.0-2026-09-19.json)。

结果也暴露了 confidence 的限制：选择候选的 confidence 为 `0.97–1.00`，但正确的
布局顺序选择最低只有 `0.43`。这与本仓库此前的置信度实验一致，不能用统一高阈值把
低 confidence 直接判为错误。

Vercel 路径仍未跑通。对 json-render 官方公开 Playground 发起请求时，HTTP 接口返回
`200`，但流内返回：

```json
{"__meta":"error","message":"Evaluation request failed (HTTP 403)."}
```

另一个 Gateway 凭据到达 evaluation endpoint 后被账户信用卡验证拦截。因此本报告的
成功结果来自 TypeSafe API 直连，不代表 Vercel Gateway 路径已复现。实验仍保留官方
`experimental_createEvaluator({ model: "typesafe-ai/jev" })` 入口。

## 复现

```sh
cd experiments/json-render-jev
npm install
npm test
npm run typecheck
npm run demo
```

真实 Jev（从仓库根目录 `.env` 读取 `TYPESAFE_API_KEY`）：

```sh
npm run demo:typesafe
```

Vercel AI Gateway：

```sh
AI_GATEWAY_API_KEY=... npm run demo:gateway
```

代码与说明见 [`experiments/json-render-jev`](../experiments/json-render-jev/README.md)。

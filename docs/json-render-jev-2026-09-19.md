# json-render 与 Jev 最小集成验证

> 日期：2026 年 9 月 19 日
>
> json-render：`@json-render/core@0.21.0`、`@json-render/react@0.21.0`
>
> 范围：官方组合与渲染链路的本地验证；真实 Jev 请求尚未完成

## 结论

官方实现可以工作，不只是概念代码。本实验复用了正式发布包中的
`experimental_composeSpec`，从应用提供的七个候选中完成两阶段选择：

1. `select` 批量选择 dashboard、订单表、指标行、三个指标和周收入图；
2. `layout` 把三个指标放入指标行，并按“订单表 → 指标行 → 周收入图”排列。

composer 生成的 flat Spec 通过 catalog 校验，随后由 `@json-render/react`
渲染为 HTML。离线回归使用确定性 evaluator，只验证 json-render 的组合、校验和渲染，
**不能代表 Jev 的选择质量或延迟**。

## 实际结果

| 检查项 | 结果 |
| --- | --- |
| composer 完成原因 | `finish` |
| evaluation 批次 | 2（`select` + `layout`） |
| Spec 元素数 | 7 |
| catalog 校验 | 通过 |
| React HTML 渲染 | 通过 |
| 结构与顺序测试 | 2/2 通过 |
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

## 真实 Jev 链路状态

本机没有导出的 `AI_GATEWAY_API_KEY`、`JEV_AI_GATEWAY_API_KEY` 或
`TYPESAFE_API_KEY`，因此未伪造真实模型结果。另对 json-render 官方公开 Playground
接口发起相同类型请求，HTTP 接口本身返回 `200`，但流内明确返回：

```json
{"__meta":"error","message":"Evaluation request failed (HTTP 403)."}
```

这说明 2026 年 9 月 19 日此次检查时，官方线上页面的 Jev evaluation 后端没有成功
获得 Gateway 授权；不能把宣传视频视为本次复现成功。实验入口保留了官方
`experimental_createEvaluator({ model: "typesafe-ai/jev" })`，配置有效的 Gateway
密钥后可原样运行真实链路。

## 复现

```sh
cd experiments/json-render-jev
npm install
npm test
npm run typecheck
npm run demo
```

真实 Jev：

```sh
AI_GATEWAY_API_KEY=... npm run demo:live
```

代码与说明见 [`experiments/json-render-jev`](../experiments/json-render-jev/README.md)。

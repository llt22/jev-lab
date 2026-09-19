# Jev 第四轮·补充报告：官方口径增量、融资事实与平台化接入核验

> 调研日期：2026 年 9 月 19 日（与主报告 `jev-round4-2026-09-19.md` 同日并行）
> 方法：X 登录态实时检索（`typesafe jev` / `jev` / `#jev` / `jev vercel`）+ 官方文档与官网直接抓取 + Vercel/LangChain/DCVC 一手页面 + PyPI/npm 可核对结构
> 关联：[主报告（独立实测与开源复现）](./jev-round4-2026-09-19.md) · [第三轮调研](./jev-round3-2026-09-18.md) · [首轮验证报告](./jev-validation-2026-09-18.md)
> 原始抓取：[X 检索结果](../artifacts/round4-2026-09-19/x-搜索结果-2026-09-19.json) · [官方与媒体核验](../artifacts/round4-2026-09-19/官方与媒体核验-2026-09-19.json)

## 本报告定位

主报告覆盖了独立第三方实测、开源复现（CUA-S1）、TechCrunch 报道与生态规模。本报告只写**主报告未覆盖**的三块：官方文档与官网的增量口径、融资与公司事实、平台化接入（Vercel / LangChain / OpenRouter）及 Vercel 采纳数据引发的社区纠偏。两者合起来才是完整的第四轮证据面。

## 1. 官方文档增量（9-18 之后可核对的新原文）

### 1.1 版本与价格：无漂移

[models 页](https://docs.typesafe.ai/models) 直接抓取确认（2026-09-19 10:30 CST）：

- 当前唯一模型仍是 `jev-1.13.0`；`jev-latest` 与 `jev-preview` 均指向它，无 preview build。
- 价格不变：`$42/Btok（$0.042/Mtok）`，输出免费；限流 250,000 token/s、1,200 req/min。
- **主报告与第三轮"固定 jev-1.13.0 评测"的策略依然有效，无需迁移。**

同一页出现两段**此前未记录的官方原文**，值得全文引述：

**Language support**（本轮最重要的官方新增）：

> "Jev accepts natural-language text. English is the primary training language and where accuracy is currently best. Other languages, including CJK scripts, are handled but not equally well; test on your own content before relying on Jev for a non-English workload, and pay close attention to Confidence when routing."

**Data handling**：

> "Jev is not trained on customer requests or responses. See Legal for the Data Processing Agreement, the Privacy Policy, and details on zero data retention (ZDR) for enterprise customers."

对 jev-lab 的意义：

1. 官方首次在文档里明确提到 **CJK**——"handled but not equally well"——这是第三轮待办里"测中文"的官方背书，且官方给的兜底建议（注意 Confidence、自行测试）与我们的置信度闸门方向一致。
2. 官方还建议 **pin 版本化 ID 而非别名，并通过响应 model 字段记录实际版本**（原文："If you have tuned confidence thresholds against a specific version, pin that version's ID instead of the alias and move to the new one on your own schedule"）——与 jev-lab 第三轮"监控版本漂移"待办完全一致。
3. 新增 `GET /v1/models` 端点说明：返回别名列表；版本化 ID 即使不在列表也可用——比第三轮多了个可核对的模型清单接口。

### 1.2 文档站新增 PATTERNS / COOKBOOKS / DEMOS 区块

[Patterns 页](https://docs.typesafe.ai/patterns) 收录了四个官方架构模式，其中两个**直接对应本仓库已跑过的实验**：

| 官方模式 | 官方定位 | 本仓库对应 |
| --- | --- | --- |
| Speculative Fan-Out | 一次请求发很多问题（含投机性问题），让代码决定相关性 | `benchmark_fanout.py`（1→20 个 Noul 延迟不增长的实测） |
| Confidence-Gated Routing | 用置信度作为第二决策轴构建更安全的系统 | `confidence-escalation-v1`（0.6–0.7 阈值放行九成决策的实测） |
| Composite Scoring | 多维分析合成一个分数 | 未直接对应 |
| Intent Routing | 意图分类后路由到处理器 | 客服分类部分 |

COOKBOOKS（Self-consistency、Batching、Extraction、Classification）与 Demos（Smart home assistant）也是此前几轮未收录的内容。**官方把这些模式写进文档，说明我们的实验方向与官方推荐一致——但官方只给模式，不给阈值校准方法，校准仍需业务数据。**

### 1.3 官方 evals 表与"三套口径并存"问题

[dev.to 对官方 evals 的转述](https://dev.to/gabrielanhaia/jev-beat-gpt-luna-by-1-point-gpt-6-and-claude-wrote-the-answer-key-314k)（Gabriel Anhaia，09-17）：

| 模型 | Accuracy | Cost / case | Latency |
| --- | ---: | ---: | ---: |
| Jev | 67.8% | $0.0004 | 0.4s |
| GPT-5.6 Luna | 66.8% | $0.0033 | 12.9s |
| GPT-5.6 Terra | 67.9% | $0.0304 | 10.1s |
| Claude Sonnet 5 | 67.8% | $0.1174 | 78.1s |
| GPT-5.6 Sol | 74.1% | $0.0836 | 23.3s |
| Claude Opus 5 | 73.1% | $0.1761 | 37.8s |

两条必读的读法：

1. **Jev 只比 Luna 高 1 个点，且低于 Sol/Opus 约 5–6 个点。** 它的卖点不是分数最高，而是同等分数下成本低 2–3 个数量级——与主报告三家独立实测的结论（"质量大致相当，无普遍优势"）在官方自己的表里也成立。
2. **官方 eval 的参考标签由 GPT-6 Astra 和 Claude Fable 5.1 平均生成，无人工标注**（"We likely underestimate our model"）；workflows 由自家能力团队构建（"some bias could exist"）；LLM 对比走自家 wrapper（"tends to be slower and more expensive"）。**这是模型互评，不是事实核对。**

同一场发布并存**三套速度倍数口径**（[agentpedia claim-by-claim](https://agentpedia.codes/blog/jev-system-one-models)）：launch tweet 20–200x / 40–400x、[首页 193.6x / 444.6x](https://typesafe.ai)（脚注 "Based On Workflows For System One Tasks"）、官方 PR "up to 100x"。官方自己承认首页数字属于 "higher end of real world gains"。**这也解释了第三轮记录的社区传播失真：失真源头之一是官方自己的三套口径。**

### 1.4 官方姿态："we love skeptics" 与关键让步

[agentpedia](https://agentpedia.codes/blog/jev-system-one-models) 整理了官方发布的配套物：

- **"we love skeptics" 板块**：官方预先发布反对自己的观点；
- **MIT 许可的复跑 adapter**：任何人可在自己的 workflow 上重跑官方对比；
- **live evals dashboard**：含 per-case disagreement walkthroughs（逐条分歧展示）。

这些姿态值得肯定，但**姿态不等于证据**：RLCD 的校准至今**没有任何公开证据**（无论文、无 reliability curve、无 ECE 数字、无消融实验；HN 上被追问而未答）。这与本仓库"官方概率必须用业务数据重新校准"的结论一致。

**本轮最值得记录的一句社区交锋**（HN，475+ 评论）：评论者说 "this is basically a zero-shot classifier"，**创始人 Almeida 回复 "exactly right!"**。一个以"新模型类"为框架的发布，创始人亲口承认其本质就是零样本分类器。它不否定 Jev 的产品化与成本价值（主报告已有独立实测支持），但**"System One 新范式"的说法在开源复现（CUA-S1，70 万参数复现契约）+ 创始人自认分类器 + 官方承认模型互评标签的三重证据下，需要大幅降温**。

## 2. 融资与公司事实（可核对）

| 项目 | 事实 | 来源 |
| --- | --- | --- |
| 轮次 | $40M **Series Seed**，DCVC 领投，2026-09-15 宣布 | [DCVC 官博](https://www.dcvc.com/news-insights/typesafe-emerges-from-stealth-with-a-new-way-of-doing-ai/) / [SiliconANGLE](https://siliconangle.com/2026/09/16/typesafe-ai-exits-stealth-with-40m-to-build-ai-for-use-by-software/) |
| 估值 | Forbes 报道 $200M（引述知情人士） | SiliconANGLE 转述 |
| 创始人 / CEO | **Diogo Almeida**，OpenAI 前研究员，参与 InstructGPT / ChatGPT / GPT-4，RLHF 共同发明者；2024 年创立 | TechCrunch（主报告 §2 同源） |
| 联合创始人 | CTO **Erik Gafni**；COO **Sasha Sheng**（ex-Meta/FAIR） | agentpedia / SiliconANGLE |
| 总部 | 旧金山 | SiliconANGLE |
| 命名 | William Stanley Jevons，19 世纪经济学家，杰文斯悖论（成本下降 → 使用量上升） | TechCrunch |
| 当前状态 | waitlist 早期访问；API 曾因需求过高短时不可用 | TechCrunch |

两点解读：

1. **$40M seed 是"证据形态"的一部分**：这解释了为何官方敢以低价 + 免费输出进入市场——"是否是补贴价"官方自己都说 "We can't prove it isn't subsidized"（agentpedia 记录）。**价格可持续性仍是开放问题，9 月 25 日 Vercel 免费期结束后的定价是关键观察点。**
2. **RLCD 无公开证据 + 护城河在数据配方的说法**（主报告 §8 判断变化第 5 条在此获得强化：创始人称"一半公司是一个拥有整个合成数据子领域的实验室"）——若架构可替代而数据配方不可替代，竞争沿数据展开。

## 3. 平台化接入（本轮最大结构变化）

### 3.1 Vercel AI Gateway（可核对的官方页面）

[Vercel changelog](https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway)（09-16，Rohan Taneja / Zachary Chen / Jerilyn Zheng）：

- Jev 已上线 AI Gateway；模型名 `typesafe-ai/jev`。
- **AI SDK 7 的 `experimental_evaluate` API** 支持 Choice / Score / Boolean 三类问题。
- `providerOptions.gateway.zeroDataRetention: true` **按请求开启 ZDR**——与官方 Enterprise ZDR 声明匹配。
- changelog 引用官方 193.6x / 444.6x 与用例清单（选下一个工具/子 agent、决定继续/重试/询问/停止、动作前评分紧急度或风险、验证模型输出与护栏）。

**免费期是本轮 X 上传播最广的事实**：多帖确认 Jev 在 Vercel AI Gateway **免费到 9 月 25 日**（[@dgrreen](https://x.com/dgrreen/status/2101134040996700287)、[@StatsWire](https://x.com/StatsWire/status/2101134037008175437)、[@unsu0707](https://x.com/unsu0707/status/2101131075502444647) 等）。这意味着**过去几天 Vercel 渠道的"爆发"无法与免费期剥离**（见 §4）。

### 3.2 LangChain 官方集成（可核对：PyPI + npm + 博客）

[《Building a Harness with Jev》](https://blog.langchain.com/building-a-harness-with-jev/)（S. Runkle / H. Lovell，09-17）与真实包：

- Python：`langchain-typesafe` 0.0.1a2（PyPI 实查，requires Python ≥3.10）：`TypeSafeClassifier` + `Noul`。
- JS：`@langchain/typesafe` 0.0.1（npm 实查）。
- 两个 experimental 中间件直接对应本仓库 agent-control 实验：
  - `ModelRouterMiddleware`：Jev 判断选哪个模型（fast/powerful），即**模型路由**；
  - `AutoModeMiddleware`：**用 Jev 检查工具调用的风险并在执行前阻断**——正是第三轮总结的"动作前否决位"模式的官方实现。
- 博客提名：Kyle Jeong（Browserbase）浏览器 agent"几分钱"、Jarrod Watts 实时交易 agent、Ryan Vogel 邮件分类（均为作者自报，无数据）。

**LangChain 官方博客 + 已发布 SDK 是最强的一类可核对结构：安装即验证。** 它同时证明生态从"第三方的自研 adapter"（第二轮记录的 system-one-adapter-python ★96）升级到了主流框架官方支持。

### 3.3 OpenRouter 合作与生态扩散

- 官方原帖 [@OpenRouter 🤝 @typesafeai](https://x.com/typesafeai/status/2100747035746193598)（09-18，1,705 赞）；评论出现"为了用 Jev 专门注册 OpenRouter"以及"OpenRouter 会不会更慢"的疑问——**后者目前无人实测**。
- [@ckaraca](https://x.com/ckaraca/status/2101120780696174712)（09-19）：Composio、vercel/ai、rig、Phoenix 均已上线 Jev 集成，"列表超过 100，每周按 star 重排"（作者自报，未逐项核验）。
- 民间渠道已领先官方：多位用户指出可直接走 OpenRouter / Vercel AI Gateway 绕过 waitlist；waitlist 通过后**自动获得 $5 额度**（[@takashimaya_dev](https://x.com/takashimaya_dev/status/2101131314313470397)、[@gosrum](https://x.com/gosrum/status/2101131109245632784) 实测）。结合 TechCrunch 的"API 一度不可用"，**更合理的解释是容量受限而非准入控制**。

## 4. Vercel 采纳数据：13% 与它的星号

Vercel 官方[发帖](https://x.com/vercel/status/2101077346203971900)（09-18）：

> Jev 的采用速度比 AI Gateway 历史上任何其他模型都要快。第一天覆盖约 13% 的团队，是 GPT-5.6 系列的 2 倍，Fable 5.1 的 6 倍。

随后出现了**五类结构性纠偏**，本轮最值得记录的社区讨论：

| 纠偏 | 来源 | 要点 |
| --- | --- | --- |
| 免费期 | [@aaliyaanX](https://x.com/aaliyaanX/status/2101129020700340434) | "免费好奇心是真实的，真正要紧的是 9 月 25 日之后的留存" |
| 任务不可比 | [@PujaraMihir](https://x.com/PujaraMihir/status/2101103627884749175) | "Jev 不写代码不写散文，不替代任何模型，只是放在旁边；day-one 份额衡量的是接入有多便宜" |
| waitlist 溢出 | [@bigmrrobert](https://x.com/bigmrrobert/status/2101111592037302363) | "所有人让 agent 配 Jev 却过不了 waitlist，就默认改用 Vercel gateway" |
| 唯一可访问渠道 | [@CyaVer009](https://x.com/CyaVer009/status/2101128232846471516) | "因为这几乎是唯一能访问的地方……" |
| 方法未公开 | dev.to 转述 | Vercel 的 5–18x（fx 安全审查器）无数据集、无样例数公开 |

这与第三轮"对官方数字同样要交叉验证"的结论同构，且**争论焦点已从模型能力转向免费期数据的解释**。引用 13% 时必须带星号。

## 5. 主报告与本报告的交叉校验

两篇同日报告在完全独立的抓取路径下得出了互相兼容的结论：

| 主题 | 主报告（独立实测/开源） | 本报告（官方/平台） |
| --- | --- | --- |
| 质量 | 三家独立评测：无普遍质量优势 | 官方 evals 表：Jev 67.8%，低于 Sol/Opus 5–6 个点 |
| 校准 | clay：yes/no 真实、1–5 量表过度自信 | RLCD 无任何公开校准证据；官方建议注意 Confidence |
| 成本 | 有独立支持；Parallel 给出反向论证 | 官方三套口径并存；"不能证明不是补贴价" |
| 中文 | 仍无有效证据 | 官方新增 Language support：CJK "not equally well" |
| 生产 | Vercel fx 5–18x（TechCrunch 转述） | Vercel changelog + 13% 采纳数据及星号 |

## 6. 更新后的下一轮优先级（与本仓库实验直接相关）

1. **实测延迟分段**（继承主报告第 1 条）：1.5s 全链路 vs 第三方 176–180ms 的差距需拆解——DNS/TLS/网关/推理分段计时。**这是修正既有结论的最直接一步。**
2. **中文/中英混合实测**（本报告新增依据）：官方明说 CJK "handled but not equally well"，且建议自行测试并注意 Confidence——第三个被官方背书的缺口。
3. **按问题类型重做校准**（继承主报告第 3 条，本报告补充）：官方 evals 标签是模型互评，我们的可核对事实方法仍是唯一不依赖模型互评的对比基准。
4. **9 月 25 日 Vercel 免费期结束**后，记录价格与留存数据——"13% 星号"的验证点。
5. **复跑 clay_shentrup 四发现**（注入、23k token、排序器、64 并发）+ 复现 CUA-S1（主报告第 2、4 条）——两者都可直接用本仓库脚本框架低成本实现。
6. **在双通道（官方 API vs Vercel Gateway vs OpenRouter）各跑一轮同一数据集**，顺带回答社区"gateway 会不会更慢"的疑问。

## 7. 附录：Theo 对"Jev 上下文压缩"策略的批评（用户转述后核实）

> 核实时间：2026-09-19 11:10 CST，登录态浏览器；原始抓取见 [`artifacts/round4-2026-09-19/theo-上下文压缩批评-2026-09-19.json`](../artifacts/round4-2026-09-19/theo-上下文压缩批评-2026-09-19.json)。

用户看到的批评来自 **Theo（t3.gg，@theo）2026-09-17 的原帖**（[status/2100762304862384257](https://x.com/theo/status/2100762304862384257)），针对当时爆火的 **fast-jev-compaction**（★3.3k，当前最大的 Jev 生态项目）——"用 Jev 逐个判断工具调用是否值得保留"式的压缩策略。他明确声明：**"我的帖子中没有任何内容与 Jev 有关，这只是关于代理和压缩是如何工作的"**（[status/2100776434210058570](https://x.com/theo/status/2100776434210058570)）——批评对象是这种压缩策略本身，不是 Jev 模型。

### 7.1 Theo 六点批评（原文语义）

1. **压缩不是过滤器**：压缩的作用是清理历史以保持代理专注，应在上下文**过长时**谨慎使用，而不是持续删除保持简短。
2. **Jev 不知道自己在决定什么**：32k 上下文模型对早期历史知之甚少；按逐行/逐工具调用决策的实现里，它甚至看不到工具调用的**结果**。随机删除会让模型不知道试过什么，注定陷入"愚蠢循环"——一遍遍重试同样的事。
3. **完全放弃推理过程**：OpenAI/Anthropic/xAI/Google 的前沿模型不会通过 API 共享推理轨迹（加密负载，Jev 看不到且常被丢弃）；**Anthropic 尤其严格，要求保留整个历史才能获取任何推理数据**——因此在 Claude Code 中使用"保证模型非常愚蠢"。
4. **模型在其压缩流程上被调优**：前沿实验室已把压缩和长运行纳入训练，模型学会的原生压缩优于任何临时方案。
5. **缓存写入比缓存读取昂贵**：cache write 常超过 LLM 总支出的 60%；历史前部任何编辑都使后续缓存失效——删除"2"必须重写"3,4,5,6"，比保留"2"更贵。
6. **"未保留即永久删除、助手可重跑工具/重读文件"是危险的默认**：祝你好运（原文 "Good luck"）。

结语原话：*"这是一个很酷的实验，我确实觉得它有趣。但如果你认为这种基于概率阈值的过滤是一种压缩策略，我强烈建议你直接使用 Claude Code 和 Codex 等工具中的默认设置——那样你更不容易伤害自己。"*

### 7.2 作者回应与交锋（09-18）

- **tamara（fast-jev-compaction 作者）**：状态在每次压缩请求中被保留，工具请求与结果**通过 tool_use_id 配对**，模型对相关/不相关有上下文；首条消息与最新 `preserveRecentMessages` 内的调用被固定不动（[status/2100769054789378301](https://x.com/tamarajtran/status/2100769054789378301) + [仓库 README](https://github.com/tamaratran/fast-jev-compaction)）。
- **Theo 反驳**：对 Anthropic 模型"工具调用可配对可见"**已不再是事实**（preserved thinking 变更，[官方说明](https://support.claude.com/en/articles/16761192-preserved-thinking-changing-how-the-messages-api-handles-thinking-blocks-to-protect-against-distillation)），其他实验室大概率跟进（[status/2100770236329062518](https://x.com/theo/status/2100770236329062518)）；"无论运行压缩的模型还是压缩后运行的模型，都无法再访问推理功能"（[status/2100772756040430029](https://x.com/theo/status/2100772756040430029)）。
- **Theo 指出的真正方向**："如果 LLM 从来不需要考虑 KV 缓存会怎样？"——即 Diogo 在回复中暗示的思路（[status/2100762775668805960](https://x.com/theo/status/2100762775668805960)）。
- **转发认可**：Stephen Brouhard："关于为什么不要用 Jev 实现这种病毒式压缩策略的绝佳解释……也许未来某种形式可以实现，但不是这个"（[status/2101108801470410923](https://x.com/ssbrouhard/status/2101108801470410923)）。

### 7.3 与 jev-lab 上下文过滤实验的对照

本仓库第一轮 `agent-control-v1` 的上下文过滤实验（关键召回 100%、压缩率 6.8%、危险误删 0，但未测删除后的任务完成率）与 Theo 批评的交集：

| Theo 批评点 | 本仓库已有证据 | 缺口（Theo 补的维度） |
| --- | --- | --- |
| 概率阈值过滤不是压缩 | 边界概率实测翻转（0.49/0.51/0.49），原结论"不能把单次低于 0.5 当作删除许可" | 未评估"删除后 agent 任务完成率"（愚蠢循环风险） |
| 缓存写入成本 | 未测 | 压缩省下的 token 可能被 cache write 吃掉甚至更贵 |
| 推理轨迹依赖 | 未测 | Anthropic 收紧后此类插件的配对信息不可见，策略会随之失效 |
| 永久删除风险 | 原结论已要求"可恢复存根或灰区队列" | Theo 认为"可重跑工具/重读文件"的默认太乐观 |

**结论：批评站得住的部分是"概率阈值过滤＝压缩"是过度简化**——永久删除、缓存失效、丢失推理链的代价真实存在；它不否定"用 Jev 做选择性保留判断"的方向（tamara 的实现确有可取之处），而是要求**可恢复设计 + 只删低风险项 + 用任务完成率而非删除率评估**——与本仓库实验结论方向一致，并把"必须可恢复"从建议升级为必要条件。

## 复现说明

本报告所有 X 检索在登录态浏览器（空间 `Jev round4 X research`）完成，原始抓取见 `artifacts/round4-2026-09-19/`；官方/媒体页面均为直接抓取，文中 URL 即证据。第三方转述（dev.to、agentpedia、creativeainews）已标注其性质；所有官方数字均未独立复现，引用时应注明口径与日期（2026-09-19 10:30 CST）。

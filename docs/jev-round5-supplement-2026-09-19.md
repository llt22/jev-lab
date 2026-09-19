# Jev 第五轮·补充：知识猫 28 案例与 jev-lab 覆盖对照

> 调研日期：2026 年 9 月 19 日（与主报告 `jev-round5-2026-09-19.md` 同日并行，用户点题后核实）
> 来源：知识猫AI实验室（@GeekCatX）[28 种玩法清单帖](https://x.com/GeekCatX/status/2100956459580395585)与[8 方向总结帖](https://x.com/GeekCatX/status/2101007181823045930)（2026-09-18）
> 目的：用第三方的 28 案例清单当"审计清单"，逐条对照 jev-lab 已有文档，找出我们漏掉的案例与方向
> 原始抓取：[`artifacts/round4-2026-09-19/知识猫-28案例对照-2026-09-19.json`](../artifacts/round4-2026-09-19/知识猫-28案例对照-2026-09-19.json)

## 一句话结论

**我们有约 14 条未覆盖（28 条中约一半），漏得最集中的是两个方向：实时交互辅助（会议观察/即时建议/自动补全/Emoji 全漏）和搜索与数据处理（图提取/PQ 搜索/SQL 扩展全漏）。** 已覆盖的集中在 Agent 调度、浏览器操作、上下文压缩、业务分流——正好是我们实验做过的方向，说明"我们测过的方向恰好是调研里最热的方向"，但生态的宽度没有被我们记录。

## 一、知识猫的 8 方向分类（第三方中文社区分类，原文要点）

| 方向 | 知识猫定义要点 | jev-lab 覆盖度 |
| --- | --- | --- |
| 1. Agent 调度 | 选模型/工具/Skill；直接处理 vs 交更强模型 vs 转人工；减少无效调用 | ✅ 实验级覆盖（模型路由） |
| 2. 记忆与上下文管理 | 筛选历史、重排检索、判断材料适用性 | ⚠️ 有批评专题（Theo），无正面案例 |
| 3. 代码与软件质量检查 | PR 审查、代码评分、QA 测试；"找出值得追加检查处" | ⚠️ PR 有，代码评分/QA 漏 |
| 4. 浏览器与电脑操作 | Browser Use、iOS 模拟器、鼠标绘图；状态→有限动作候选→选下一步 | ✅ jev-browser/voice-browser |
| 5. 业务分流与内容审核 | 工单/意图/社区审核/复核排序；"商业落地最扎实" | ✅ 我们的主战场 |
| 6. 搜索与数据处理 | 自然语言筛选、实体匹配、图提取、SQL 扩展 | ❌ **全漏** |
| 7. 实时交互辅助 | 会议观察、即时建议、自动补全、预测启动器、Emoji | ❌ **全漏**（预测启动器除外） |
| 8. 游戏与复杂控制实验 | Minecraft、自动驾驶、交易 | ⚠️ 官方 Doom 有，Minecraft/自动驾驶漏 |

知识猫的判断："最先规模化的会是 Agent 调度、业务分流、记忆筛选和质量检查——判断高频发生、候选范围有限、需要理解语境、错误可发现可补救。"
（他引用后期维特根斯坦："理解语言要看它在具体活动中的使用，同一个'紧急'在客服、会议和代码故障里对应不同的处理方式"——与 Jev 需要业务状态上下文的设计观一致。）

## 二、28 条逐条对照（✅已覆盖 / ⚠️部分 / ❌漏）

| # | 玩法 | 作者 | 覆盖 | 核实要点（漏项的原文） |
| --- | --- | --- | --- | --- |
| 1 | 模型路由 | mdhafir 等 | ✅ | agent-control 路由实验 + Antonio Leiva 缓存实测 |
| 2 | 实时控制浏览器 | moritzkremb | ✅ | §9 语音控制家族 |
| 3 | **记忆路由** | moritzkremb | ❌ | "令牌减少 94%，记忆检索快 2–3 倍"（快速测试） |
| 4 | PR 审查 | redp314 | ✅ | round5 §一.5（14 检查/$0.00007/0.5s） |
| 5 | **Discord 审核** | brainstormity | ❌ | **Jev-Moderation-Bot（开源）**：四阶段渐进升级（警告→10 分钟超时→1 小时超时）、双重审计日志、管理员两步确认、一键赦免即时学习 |
| 6 | Browser Use | VladTerin | ✅ | Cline jev-browser |
| 7 | **任意语言语法高亮** | imarikchakma | ❌ | "可高亮任何语言，甚至我编造的语言" |
| 8 | **AI 文本检测** | Totzenberger | ❌ | "比 pangram 便宜 6000 倍，性能相当且快得多" |
| 9 | 货币和股票交易 | BrendanPlayford | ⚠️ | round4 主报告提过 jev-trader/trading agent，该帖未单独核实 |
| 10 | 超快 Computer Use | milindlabs 等 | ✅ | CUA-S1 |
| 11 | **实时 AI 建议** | ctnicholasdev | ❌ | "每次编辑单元格做 20+ 智能检查即时警告，无需 LLM" |
| 12 | **自动补全** | miiura | ❌ | "输入时理解意图和参数，就绪即提前执行，无需等回车" |
| 13 | **代码质量打分** | niazmorshed_ | ❌ | **jev-review（MCP 插件）**：代理工作时调 Jev 评分→改进→循环 |
| 14 | **QA 测试** | krzysztof_moch | ❌ | "雇 Jev 当 QA 测试员" |
| 15 | **Minecraft** | JustLingonberry | ❌ | "1 美分玩 2 分钟（150k tokens），自动知道夜幕降临时躲僵尸，无需提示" |
| 16 | iOS 模拟器控制 | camsoft2000 | ❌ | 未单独核实（电脑操作类） |
| 17 | **图提取** | yoheinakajima | ❌ | babyAGI 作者：逐词语义重要性打分（1–5）+ 相关词 ID + 高分词知识图 |
| 18 | **胡说八道禁言麦克风** | Sybuilds | ❌ | "胡说八道时把你静音"（演示） |
| 19 | 上下文即时压缩 | tamarajtran | ✅ | §7 Theo 批评专题 |
| 20 | 预测启动器 | dabit3 | ✅ | round5 §二 jev-launcher |
| 21 | **自然语言 PQ 搜索** | iam_zachi | ❌ | **jev() PostgreSQL 扩展**：无索引无嵌入 `WHERE jev(people, 'could work from home')`；129 行约 1 秒 $0.0009，二次运行 6ms 缓存 |
| 22 | **基于 Jev 的编程语言** | southpolesteve | ❌ | **Probably 语言**：Jev 嵌入语言——feels 提问题、match 路由描述、while 直到"不再感觉正确"；Jev 决策 + LLM 写作 + 代码拼接（作者自称玩具） |
| 23 | Excalidraw 鼠标绘图 | VladTerin | ❌ | 帖子无正文可抓，未核实 |
| 24 | **Emoji 候选** | riku720720 | ❌ | "100–200ms 响应；选项 3 种或 200 种响应速度不变"——**fan-out 并行性的直接佐证** |
| 25 | 机筛简历（官方案例） | 官方 composite-scoring | ⚠️ | 模式已记录，官方案例细节未展开 |
| 26 | **实时会议观察** | tsuyoshi_osiire | ❌ | "发言时更新 探索↔收束、解消↔未决、未合意↔合意 三维度可视化会议"；可用于用户访谈实时解析 |
| 27 | **特斯拉自动驾驶** | jpschroeder | ❌ | "一小时内重建特斯拉 FSD"（概念 demo 级） |
| 28 | **筛选 SQL 扩展** | iam_zachi | ❌ | "普通英语转 WHERE 子句，逐行判断，无索引无嵌入" |

## 三、漏掉案例里值得注意的

1. **iam_zachi 的 SQL 扩展是最有"可核对事实"价值的案例**——`WHERE jev(people, 'could work from home')` 这种"逐行判断 + 无嵌入"的设计，正好可以用我们第三轮"可核对答案"的方法去实测（判断对错完全可验证），是下一轮实验的好素材。
2. **riku720720 的 Emoji 候选**直接佐证了 fan-out：3 种与 200 种选项响应速度不变——与我们 benchmark_fanout 的实测（1→20 问题延迟不增长）同构。
3. **Discord 审核 bot 是少数"带审计设计"的社区实现**：四阶段渐进升级 + 双重日志 + 赦免学习——比大多数 demo 更接近生产形态。
4. **Probably 编程语言**代表一个独特方向：把 Jev 做成语言关键字（feels/match/while），"Jev 决策 + LLM 写作 + 代码拼接"三层分工。
5. **yoheinakajima 的图提取**（babyAGI 作者）是知识图方向，与官方 use-case map 的"Graphs and knowledge graphs"对应。

## 四、对我们文档的修正

- round5 主报告说"真实使用者集中在五类场景"——**知识猫清单证明生态的宽度远超五类**：实时交互辅助、搜索/数据处理、代码质量检查都是活跃方向，只是我们当时没检索到这些帖子。
- 我们文档的盲区与其说是"分类"不如说是"检索策略"：round5 用 "building / I built / using" 关键词，漏掉了**没有"构建"动词的中文/日文帖子**和**演示类帖子**（Minecraft、麦克风、自动驾驶）。
- 建议下一轮补测：SQL 逐行筛选（可核对）与"实时交互"延迟（会议观察/自动补全对误打扰率的要求）。

## 复现说明

全部帖子在登录态浏览器逐条抓取（空间 `geekcat 28 cases verify`）；28 案例的来源清单见知识猫原帖，逐条核实结果与原文摘要见 `artifacts/round4-2026-09-19/知识猫-28案例对照-2026-09-19.json`。

## 五、补录：Jev-cu——把 Computer Use 的"下一步点哪里"交给 Jev

> 用户点题后核实，2026-09-19；原始抓取见 [`artifacts/round4-2026-09-19/jev-cu-项目-2026-09-19.json`](../artifacts/round4-2026-09-19/jev-cu-项目-2026-09-19.json)。

[Sac-Y/Jev-cu](https://github.com/Sac-Y/Jev-cu)（★12，JavaScript，12 小时前更新）：**Jev 从界面文字候选中选元素/动作/完成度/风险，Codex Computer Use 负责读取界面与执行，本地策略门槛拦截敏感操作。只传文字，不传截图。**

与 Cline jev-browser 同范式（决策/执行分离、纯文字输入、代码门槛），但执行层是**桌面级**（Codex 桌面 App 的 cua_repl 运行时）而非浏览器：

- **四问标准循环**：`decide()` 每次发 target / action / done / risk 四个问题的 systemone 请求；`sanitizeLabel` 清洗 URL 噪声并截断 120 字符控 token
- **策略门槛 `policy.mjs`**（纯函数、可单测）是本项目最有价值的部分：
  - 敏感标签模式表（中英）：delete / send / payment / auth / share / install / settings → 一律 confirm
  - 五档阈值：done ≥0.9 结束；风险 ≥0.2 停下确认；目标置信度 <0.3 直接停、<0.5 升级（重试/看图/问人）；低风险 App（计算器/日历/文本编辑/Figma）放宽到 0.4
  - App 白名单（新增 App 必须显式修改）；verdict 五态 proceed/done/confirm/escalate/stop
- **安全**：默认 dry-run；界面文字只作数据不作指令；不绕过登录/付费墙/验证码；删除/发送/支付类停在 confirm
- **评测**：`p0-eval.mjs` AX 快照选元素准确率（离线、需 key）；`npm test` 单测不调用 API
- **模型口径**：`DEFAULT_MODEL = "jev-latest"`（未 pin 版本——与 jev-lab"固定 jev-1.13.0"建议不一致，注意）

归档价值：与 trycua CUA-S1（70 万参数复现 Jev 契约）正交——CUA-S1 是"用开源替代 Jev"，Jev-cu 是"用 Jev 驱动桌面 Computer Use"，把第三轮 agent-control 的"上下文过滤/语义寻路"范式扩展到桌面操作层；且其 policy.mjs 的阈值分档设计（低风险 App 放宽 + 敏感词 confirm）是把 Jev 概率接到真实安全边界的教科书式写法，值得 jev-lab 下一轮"阈值即策略"实验参考。

## 六、补录：yibie（@yibie）——awesome-jev 生态巡检员

> 用户点题后核实，2026-09-19；原始抓取见 [`artifacts/round4-2026-09-19/yibie-awesome-jev巡检-2026-09-19.json`](../artifacts/round4-2026-09-19/yibie-awesome-jev巡检-2026-09-19.json)。

[yibie](https://x.com/yibie)（**awesome-jev 索引维护者**，github.com/yibie/awesome-jev，巡检帖提及 ★454）——round4 主报告已记录他的索引（★182，"已取代此前记录的最高星索引"），本轮补的是他作为"巡检员"的三条长帖（46→61→100→108→130→160 条的生态增长过程），**这些帖子本身是生态数据源**：

**他给出的最有价值的新数据（此前未收录）：**

1. **fast-jev-compaction 正面实测**（我们此前只有 Theo 批评侧）：Claude Code **156,000→62,000 tokens，上下文使用率 78%→31%，16 条里 10 条原文保留**——作者方数据，与 Theo 批评并存，正反两面的证据现在齐了；Theo 反对帖 2,276 赞。
2. **既有主流框架接入 Jev（注意：json-render 不是 Jev 生态新长出的项目）**：**vercel-labs/json-render ★16,553**（生成式 UI 框架，"The Generative UI framework"，**2026-01-14 创建**，早于 Jev 发布 8 个月；Jev 是其 9 月新接入的 compose 路径组件/动作选择能力——属"老框架接入 Jev"，非生态新生项目，按星数是最大的 Jev 生产集成）、vercel-labs/fx ★3,057（Zig coding agent，内置 `typesafe_permission_reviewer`，即 TechCrunch fx 命令审查器的实现本体）、vercel-labs/ai-python ★183。
3. **创意新形态**：**jevinci**——让 Jev **并行预测每个像素的颜色**来作画，置信度决定笔触宽度（像素级 fan-out）。
4. **数据层**：jev() PostgreSQL 扩展（与知识猫清单 #21 同源）+ **DuckDB 扩展**（任意 CSV/Parquet 逐行分类，1000 行约 10 秒）。
5. **开源复刻全家桶**（CUA-S1 之外的第二波）：jaredpalmer/kev ★125（Qwen2.5-0.5B，MacBook 可训练）、NanoJev ★165（0.6B，完整概率分布、零 token 解码）、中文社区五款（Laya 421M / Decider-2B / NanoJev / Reflex / System-One 4B）、Qwen3.6-35B-A3B 兼容 API、"把任意 HF 模型 Jev 化"库——**接口契约的复刻已经从"可能"变成"泛滥"**。
6. **成本对照三组**：724 条广告拆解 9 分钱；3M 回放事件→$2.17（132 次暴怒点击、213 个修复 PR）；384 条新闻→$0.19（同期 Opus 5 只跑 4 条花 $0.77）。
7. **反方观点（新）**：@jiayuan_jy"更快的通用分类器，LLM 完全可以做到"；**@anderslie"快的关键是并行解码推理技术，任何开源权重模型改推理引擎都能暴露类似接口"**；@iwashi86 约 1 万次 API 调用反推内部结构；@0xBOYD"X 热火朝天但 Reddit 只有 3 条帖子（2 条还是自发）——渠道不同结论不同"。
8. **收录治理规则**（与第三轮"生态索引不可轻信"互证）：同一作者滚动 7 天 3 条上限、共同发布日期视为风险信号、明说"160 条里有大量 0 星一天写完的仓库，README 数字不一定有出处，采用前自己跑一遍"。

**归档价值**：① fast-jev-compaction 的正反两面证据齐了（作者 156k→62k vs Theo 六点批评），引用该插件时必须两方并述；② json-render 是第一个 ★万级 的 Jev 生产集成，说明"Jev 挑 UI 组件"已进入主流框架；③ 复刻潮从"能否"进入"泛滥"，进一步支持 round4"产品形态不是壁垒、护城河在数据配方"的判断；④ @anderslie 的"并行解码"观点值得记入"为什么快"的假说清单（与官方架构不公开并置）。

**补录（9-17 第一份 46 条清单中的新项目，用户点题后核实）：**
- **Notra ★170**：生产环境用开关把分类器从 LLM 切到 Jev，目标 **300ms p50**——罕见的生产替换案例（与 Vercel fx 替换 Luna 并列，但这是第三方产品自报）
- **vercel/eve**：把 typesafe-ai/jev 作为默认 eval 模型——Vercel 自家产品选型，可核对
- **browser-use/jev-ultrafast ★1046**（tagline "i. am. speed."）：知名开源浏览器 agent 库 browser-use 的 Jev 分支，用 Jev 决定浏览器每一步——注意 round3 记录过"同一 jev-ultrafast 在不同索引 star 数对不上"（2.7k vs 3533），本轮 yibie 抓取为 1046，**再次印证 star 数不可跨源比较**
- 马里奥、MuJoCo 无人机、星际争霸用 Jev 做决策——游戏/仿真决策向

## 七、X 追新线索（用户指示后主动检索，2026-09-19 15:00）

> 原始抓取见 [`artifacts/round4-2026-09-19/x新线索-2026-09-19.json`](../artifacts/round4-2026-09-19/x新线索-2026-09-19.json)。

### 1. supa Lab 独立测试：Jev vs 4 个轻量 LLM（本轮最高质量的可核对实验）

[supa Lab（日本 supa 株式会社 R&D）《Jevはどれだけ優秀なif文か》](https://journal.supa.ai/jev-classifier-benchmark/)（2026-09-18）：**同一 harness、4 任务 208 例、Vercel AI Gateway 统一调用**，指标含 accuracy/ECE/conf≥0.9 门控精度/成本/延迟。这是目前最干净的一手对比，直接回答我们首轮"与开源小模型比"的未验证项。

| 结论 | 数据 |
| --- | --- |
| 精度与轻量 LLM 相当 | Jev：support 100%、doom 两项 100%、routing 95%（落 2 问，置信度 0.36/0.76）；Luna 最佳 |
| 延迟约 3–4 倍快 | Jev p50 330–350ms / p95 520–630ms；轻量 LLM p50 930–1430ms |
| **成本输给 Qwen3.7 Flash** | Jev $0.022–0.033/千件 vs Qwen3.7 Flash $0.012–0.023——"安さだけなら選ぶ理由は弱く，精度・速度・確信度をまとめて見たときにJevが残る" |
| **校准是真实优势** | Jev ECE 0.001–0.047，conf≥0.9 时精度 100%（覆盖 92.5%）；Qwen/Gemini 误答仍自报 0.95–1.0（ECE 0.12–0.16）——"LLM 的自我申报置信度不适合做阈值" |
| 官方"数值弱项"未复现 | doom-numeric 64/64 全对（整数阈值比较）；作者注明大数/日期/聚合未测 |
| 日语无劣化 | Jev 日语 20 件全对（英语反落 2 问）；Qwen3.7 Flash 日语明显弱 |
| schema 保证不构成优势 | 5 模型强制 JSON schema 后全部零违反 |
| 边界模糊任务仍存败绩 | anisselbd/jev-phishing-bench：2000 条钓鱼邮件 Jev 输给 Haiku 4.5 |

**对 jev-lab 的直接价值**：① "conf≥0.9 → 100% 精度、覆盖 92.5%"与我们置信度闸门（0.6–0.7 阈值放行 91.7% 全对）**互相印证**——两个独立实验在高确信门控上结论一致；② "有几千标注自训 ModernBERT 更便宜"（xlm-roberta-large LoRA 94.2% vs Sonnet 4.6 85.3%、12ms vs 2s）是唯一同时给出"Jev 反面"与"何时该用传统分类器"的可执行建议；③ 成本结论 + Parallel AI 的反向论证，共同推翻"Jev 一定更便宜"的默认假设。

### 2. ToS 曾禁基准测试，官方承认修复

[@langstonnashold](https://x.com/langstonnashold/status/2100821545216303129)（credit @conjfrnk，09-18）指 Jev ToS 禁止基准测试；TypeSafe 的 [Eugene Shvarts @mathfax](https://x.com/mathfax/status/2101215621619028063) 回应 "We're fixing this! That's an outdated constraint from pre-launch."。**核验**：抓取时刻 typesafe.ai/terms 与 docs.typesafe.ai/legal 均已无 benchmark 字样。事件本身值得记录——发布前遗留条款 + 快速修复，也解释了为什么独立基准稀缺。

### 3. JevBench v1（Benchmark Heaven）筹备中

[@airesearch12](https://x.com/airesearch12/status/2101216843839004808)（Florian S，@benchmarkheaven）："Jev 类模型的第一个基准 JevBench v1，计划今天上线首个 leaderboard"。抓取时刻 benchmarkheaven.com 仍是 BETA（117 benchmarks / 844 models），JevBench 未上架——**候选监测对象**（若上线，可作为我们校准实验的对照榜单）。

### 4. Aditya Grover：Jev 可能是扩散 LLM

[Mercury 作者 @adityagrover_](https://x.com/adityagrover_/status/2101223416988840293)：Jev+Mercury 2.5 在 WebMCP 基准接近满分；"怀疑 Jev 本身是扩散 LLM——并行生成结构化输出类似 dLLM 采样时填充"。与 @anderslie"并行解码推理技术"同向，与官方"架构不公开"并置为**假说**（未证实）。

### 5. 其他小线索

- **rubikjev**（[@_trou3](https://x.com/_trou3/status/2101209823790711161)，github.com/0xtrou/rubikjev）：Jev 0.5s 解 3x3 魔方（fun demo）
- **@i_mika_el**：免费期至 9/25 窗口太紧，"周末真正动手后 Jev 在基准外还能不能立住"——与我们的 9/25 观察点一致
- 日文 [技術情報Wiki](https://x.com/tech_wiki/status/2101215430220349759) 转引了 supa Lab 文章；DevelopersIO 另有一例 NVIDIA NeMo Switchyard 难度路由替换（40/40 全对，p50 0.64–0.67s vs Gemini 2.1s / DeepSeek V4 Flash 7.2s）

### 6. 克隆地图：96 小时五款开源复刻 + 上下文天花板（第二批追挖）

> 原始抓取见 [`artifacts/round4-2026-09-19/x新线索二批-2026-09-19.json`](../artifacts/round4-2026-09-19/x新线索二批-2026-09-19.json)。

[Simeon Li（RoboKrunch）的克隆全地图](https://robokrunch.com/post/jev-open-source-clones-96-hours)：启动 4 天→HF 上 5+ 复刻、1 个 ONNX 转换、有人笔记本 CPU 跑基准。按社区热度：

| 克隆 | 热度 | 要点 |
| --- | --- | --- |
| harshatheg/Qwen-2.5-1B-RLCD | 397👍 Apache-2.0 | MLX 调优，并行约束解码比自回归快 5.6–7x（M4 Max：420ms→75ms；28 字段 triage 1900→270ms），语法有效性 100% |
| **convaiinnovations/laya** | 180👍 | **自带 evals 含校准数字 ECE 0.030 in-task——"TypeSafe 从未发布的指标"；单问题 p50 38.4ms** |
| AlexWortega/openjev | 152👍 MIT | Qwen3.5-4B cross-encoder 零样本玩 Doom（文本状态 + 原始像素） |
| 长尾 | — | DeBERTa-v3-large 变体、LFM2.5 RLCD、Qwen3-0.6B RLCD、Mattepiu/laya-onnx |

**关键对话：**Sense Noped Out 对"他们已经把 Jev 搞定了"的修正——**Laya 只有 512–1024 token 上下文（322–421M encoder），塞不下 Jev 规模的 64k state + fan-out**。契约可复刻，但状态规模的天花板不同。Simeon 的读法："1B 判断模型是周末项目，护城河从来不是权重而是分发；这些是 CPU/NPU 负载、INT8 友好，属于 edge-silicon 故事。"

**对 jev-lab 的价值**：① 开源复刻第一次带来**校准数字**（Laya ECE 0.030）——比 TypeSafe 自己还早发布 ECE；② "克隆在笔记本上跑路由"与社区 13% 分发论点连起来，进一步支持 round4"护城河在数据配方与分发、不在权重"；③ 上下文天花板（512–1024 vs 64k）是反方限定，引用"复刻搞定一切"时必须带这个边界。

### 7. Gomoku harness：代码剪枝 + Jev 短名单（教科书组合）

[Vacek 的五子棋 harness](https://x.com/VacekvVita/status/2100609341145465325)：不要求 Jev 评估全部 225 步——代码先做战术工作（检测胜/挡/分叉/断裂四连），缩到约 40 候选并按战术层排序（S 强制/A 威胁/B 攻防/C 位置），**Jev 只在短名单上选**。Antonio Coppe 评论："这是正确的形态——代码做便宜的战术剪枝，Jev 只在短名单上选；全问 225 步既浪费又是问错了问题。失败模式：当 S/A 空且 B 长得差不多时，别信 top Choice。"

**与本仓库的互证**：① 这正是我们反复的"代码保存可计算部分、模型只做语义判断"；② '别信 top Choice'与置信度闸门结论一致；③ 40 候选短名单与我们"选择集可控"的观察同构。

### 8. 其他（第二批）

- **Yonatan Gross 三天生产实录**：Map → Shadow → Measure → Promote（影子模式对照再切换，明言含漏判）——"生产切换前先影子运行"的做法值得写进我们 Phase 1 的 A/B 设计
- **@osanpochuudayo**："校准是硬部分。谁验证过那个概率是 decision-grade？你的代码可以按输出分支，Jev 能证明分支该触发吗？"——与本仓库核心立场完全一致
- **Jev Model Router mod for Claude Code**（@shipfrontierai）：非对称置信度条 0.3/0.6 控制花费，主模型路由默认关
- **Codex 重置审判**（@NFT_Chen）：社区用 Jev 做"关键词初筛 → Jev 结构化审计"判 Tibo 会不会按重置按钮——玩梗，但管线形态是标准两段式

### 9. 第三批追挖：产品形态、中文盘点与 SQLi 实测

> 原始抓取见 [`artifacts/round4-2026-09-19/x新线索三批-2026-09-19.json`](../artifacts/round4-2026-09-19/x新线索三批-2026-09-19.json)。

**① Greg Isenberg 的 10 个 Jev 原生产品**（[@gregisenberg](https://x.com/gregisenberg/status/2101284640828915995)，LateCheckout 创始人）：按"快速低成本决策对产品的改变程度"排名——代理支出防火墙、自愈工具调用、不可逆行动检测器、动态权限引擎、**代理分支修剪**（Jev 并行评分杀死弱分支）、生产事故控制器、实时谈判策略、自主退款台、实时市场调度、**基于置信度的人工队列**（"一个人监督数千自主工作流"）。收尾："LLM 生成可能性。Jev 决定下一步发生什么。"——**这套清单几乎是官方 use-case map 的产品化演绎**：防火墙/检测器/事故控制器都是"动作前否决位"、分支修剪是 fan-out、置信度队列就是我们闸门实验的产品形态。

**② G哥的中文项目盘点**（[@goan999999](https://x.com/goan999999/status/2101284406359179732)）：一次给出 10 个新仓库——jev-ultrafast（Browser Use 高速版，Google Flights 搜索 7.1 秒）、**jev-desktop**（桌面自动化决策层，与 Jev-cu 同向）、**Jev Codex Router**（0xNatoshi：回放 237 个真实 turn，成本约降 60%）、**neo4jev**（Neo4j 创始人 jexp 出品：知识图谱候选路径打概率 + Beam Search）、Blink（大代码库先判相关目录）、Winnow（上下文垃圾输出筛子）、jev-mcp、typesafe-mcp、Prism（流动性 agent）、Jev Review（devagrawal09 版）。

**③ 两个路由成本结论并存**：0xNatoshi 成本 -60% vs Antonio Leiva 缓存命中 99.35%→32%——同是"Jev 做模型路由"的实测，方向相反；**引用时必须并列，在自己的数据上验证**（差异可能在实现细节：是否按对话复用模型、是否算缓存惩罚）。

**④ SQL 注入分类实测**（[@codkobytov](https://x.com/codkobytov/status/2101276458396131480)）：1000 条 SQLi 分类 86.6%、3 美分（Kaggle 数据集）——可核对任务实例；86.6% 对安全闸门偏低，若用于拦截需更高阈值（与"概率不是生产准确率"一致）。

**⑤ 其他**：Vyacheslav 的安全边界金句（"类型安全防止畸形输出，不防止错误判断"——与我们的 schema 合规记录一致）；SEO 全站健康检查 37 秒；React 国际象棋 + Jev 落子建议；医疗救助匹配伦理视角（@pbaxm）；白名单一天通过（官网申请，与"容量受限非准入控制"判断互证）。

### 10. 🚨 JevBench v1.2 上线——首个 Jev 类模型基准（2026-09-19 当天发布）

> 原始抓取见 [`artifacts/round4-2026-09-19/jevbench-v1.2-榜单-2026-09-19.json`](../artifacts/round4-2026-09-19/jevbench-v1.2-榜单-2026-09-19.json)。

[@benchmarkheaven（Florian S）](https://x.com/airesearch12/status/2101311769113178270) 在今天（9-19）发布了 **JevBench v1.2**——"第一个 Jev 类模型基准"：15 系统 × **534 决策**（72 easy / 96 standard / 146 judge / 220 hard），德国服务器串行、单请求；harness/规则 MIT 开源、结果带 sha256 校验。**官方 Jev 不给自己评分（"no Jev grading Jev"）**——与 TypeSafe 自家 eval 的模型互评标签形成对照。

**综合分 = (Intelligence × Calibration × Speed × Cost)^(1/4)，四轴 25% 几何均值（弱轴拖垮总分）：**

| 名次 | 系统 | 综合 | I | C | S | K | $/千决策 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Jev 1.13.0** | **75.3** | 90.4 | 82.7 | 83.3 | 51.7 | $0.041 |
| 2 | **SemIf（Qwen3.5-4B 开源复刻）** | **74.6** | 85.9 | 72.6 | 83.7 | 59.2 | ~$0.023 |
| 3 | open-alternative-jev | 69.8 | 75.6 | 63.2 | 83.5 | 59.6 | ~$0.022 |
| 7 | GPT-5.6 Luna (low) | 66.0 | **96.8** | 89.8 | 77.5 | 28.2 | $0.247 |
| 11 | DeepSeek V4.1 Flash | 58.1 | 96.1 | **96.7** | 71.6 | 17.1 | $0.579 |

**六条关键结论：**

1. **开源复刻只差 0.7 分**：SemIf（启动 4 天内的 Qwen3.5-4B 复刻）74.6 vs Jev 75.3——"Jev still in the lead, but it's close"（作者原话）。对"护城河在模型能力"是重击，支持"护城河在分发/数据配方"（round4 判断再获一个独立数据点）。
2. **Luna Intelligence 全场最高（96.8）却排第 7**：几何均值让 $0.247/千决策的成本分 28.2 把准确率买不回来——这个基准的设计哲学就是"成本与校准和智力同等重要"。
3. **DeepSeek V4.1 Flash Calibration 96.7 全场最高仍排 11**：校准好不意味着整体赢。
4. **选项顺序敏感性（方法论要点）**：open-alternative-jev 把选项从 (A.no, B.yes) 翻成 (A.yes, B.no)，同一模型从 **72% 掉到 21%**——小模型对选项顺序极端敏感。**对我们自己的评测是待办：support-routing 等脚本的 Choice 选项顺序没有做鲁棒性测试。**
5. **Jev 校准分 82.7 不是最高**（Luna 89.8 / DeepSeek 96.7 更高）——我们的"Jev 校准真实优势"表述需要细化：相对轻量 LLM 成立（supa Lab 证据），相对强 LLM 不成立（JevBench 证据）。
6. **发布与 ToS 争议交织**：官方声明"禁止基准测试"条款是 outdated（@mathfax）后，JevBench 当天上线——事件链完整：conjfrnk 发现 → langstonnashold 指控 → mathfax 承认修复 → Florian 发布。

同步补录：**NanoGPT 上线 Jev 1.13 Decisions API**（[@NanoGPTcom](https://x.com/NanoGPTcom/status/2101305559064494226)：/v1/decisions，API-only——又一个平台通道）；**Hashly 生产案例**（[@hashly_h](https://x.com/hashly_h/status/2101312857463783934)：Jev 去除重事件——SIBOS 2026 重复提交 93% 相似即拒、语义搜索、Hedera 新闻过滤、mindshare 统计——已上线产品，非 demo）。

**下一轮待办（新增）**：① 我们的评测脚本补"选项顺序鲁棒性"；② 用 JevBench 的硬档题目（MIT 开源）跑一遍我们自己的校准实验作交叉验证；③ 跟踪 SemIf 后续（复刻逼近会持续发生）。

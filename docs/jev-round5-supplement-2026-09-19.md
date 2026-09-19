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
2. **平台级接入新增大户**：**vercel-labs/json-render ★16,439**（生成式 UI 框架，compose 路径用 Jev 挑组件和动作——按星数算目前最大的 Jev 生产集成）、vercel-labs/fx ★3,057（Zig coding agent，内置 `typesafe_permission_reviewer`，即 TechCrunch fx 命令审查器的实现本体）、vercel-labs/ai-python ★183。
3. **创意新形态**：**jevinci**——让 Jev **并行预测每个像素的颜色**来作画，置信度决定笔触宽度（像素级 fan-out）。
4. **数据层**：jev() PostgreSQL 扩展（与知识猫清单 #21 同源）+ **DuckDB 扩展**（任意 CSV/Parquet 逐行分类，1000 行约 10 秒）。
5. **开源复刻全家桶**（CUA-S1 之外的第二波）：jaredpalmer/kev ★125（Qwen2.5-0.5B，MacBook 可训练）、NanoJev ★165（0.6B，完整概率分布、零 token 解码）、中文社区五款（Laya 421M / Decider-2B / NanoJev / Reflex / System-One 4B）、Qwen3.6-35B-A3B 兼容 API、"把任意 HF 模型 Jev 化"库——**接口契约的复刻已经从"可能"变成"泛滥"**。
6. **成本对照三组**：724 条广告拆解 9 分钱；3M 回放事件→$2.17（132 次暴怒点击、213 个修复 PR）；384 条新闻→$0.19（同期 Opus 5 只跑 4 条花 $0.77）。
7. **反方观点（新）**：@jiayuan_jy"更快的通用分类器，LLM 完全可以做到"；**@anderslie"快的关键是并行解码推理技术，任何开源权重模型改推理引擎都能暴露类似接口"**；@iwashi86 约 1 万次 API 调用反推内部结构；@0xBOYD"X 热火朝天但 Reddit 只有 3 条帖子（2 条还是自发）——渠道不同结论不同"。
8. **收录治理规则**（与第三轮"生态索引不可轻信"互证）：同一作者滚动 7 天 3 条上限、共同发布日期视为风险信号、明说"160 条里有大量 0 星一天写完的仓库，README 数字不一定有出处，采用前自己跑一遍"。

**归档价值**：① fast-jev-compaction 的正反两面证据齐了（作者 156k→62k vs Theo 六点批评），引用该插件时必须两方并述；② json-render 是第一个 ★万级 的 Jev 生产集成，说明"Jev 挑 UI 组件"已进入主流框架；③ 复刻潮从"能否"进入"泛滥"，进一步支持 round4"产品形态不是壁垒、护城河在数据配方"的判断；④ @anderslie 的"并行解码"观点值得记入"为什么快"的假说清单（与官方架构不公开并置）。

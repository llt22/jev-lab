# Jev / TypeSafe AI — Factual Verification Report

**Verification date:** 2026-09-18, ~08:56–09:30 UTC
**Method note:** `web_fetch` could not be used for GitHub — this environment's DNS resolves `github.com` and `raw.githubusercontent.com` to `198.18.0.15` (non-public), which the fetch tool rejects. All GitHub/registry data below was obtained with `curl` and an authenticated `gh` CLI (`gh api`), which reach the network normally. npm/PyPI data came from `registry.npmjs.org` and `pypi.org` JSON APIs.

---

## 1. Official TypeSafe "skill" package — CONFIRMED (with one caveat)

**Repo exists: `https://github.com/typesafe-ai/skills`** — [source](https://github.com/typesafe-ai/skills)
- Description: "Agent skills for building with TypeSafe's System One API"
- ★146 · forks 10 · license MIT · language n/a · created `2026-08-24T23:58:39Z` · **pushed (last content update) `2026-09-12T05:42:06Z`**
- Commit history is only **2 commits**: `2026-08-25T00:23:24Z` "Initial commit" (`619f78a`), `2026-09-12T05:42:05Z` "Release v0.5.7" (`65a39f3`). Repo-level `updated_at` is 2026-09-18, but that reflects metadata/star activity, not content.

**Full file list (7 blobs, from `git/trees/main?recursive=1`):**

| Path | Size |
|---|---|
| `.claude-plugin/marketplace.json` | 382 B |
| `.claude-plugin/plugin.json` | 320 B |
| `LICENSE` | 1068 B |
| `README.md` | 1336 B |
| `skills/typesafe-ai/LICENSE` | 1068 B |
| `skills/typesafe-ai/SKILL.md` | 10040 B |

Plugin manifests declare name `typesafe`, version **0.5.7**, author "TypeSafe AI", `https://typesafe.ai`.

**Install commands, exactly as documented** ([repo README](https://github.com/typesafe-ai/skills) and [docs.typesafe.ai/agent-skill](https://docs.typesafe.ai/agent-skill)):

```bash
# Claude Code plugin
claude plugin marketplace add typesafe-ai/skills
claude plugin install typesafe@typesafe-ai

# Other agents via skills.sh
npx skills add typesafe-ai/skills --skill typesafe-ai
```

The claim in the prompt is **correct as documented**. Updates: `claude plugin marketplace update typesafe-ai` / `npx skills update`.

**What SKILL.md tells an agent to do** (read in full, 10 KB, no executable code — pure instructions):
- Front matter: `name: typesafe-ai`, MIT, long description covering Choice/Score/Noul judgements for routing, ranking, extraction, verification.
- Treats **`https://docs.typesafe.ai/llms.txt` as source of truth** and instructs the agent to read live docs during the task (Mintlify serves Markdown by appending `.md`).
- Maps tasks → doc pages (System One, state, primitives, confidence, HTTP API, Python/JS SDK, migration guide).
- Design rules: keep rules/calculations/lookups/side effects **in code**; supply semantic understanding from the model; put the judgement in `instructions` and answers in `criteria`; question IDs are not sent to the model; one narrow coherent judgement per question; combine independent questions over shared state (they run in parallel and cannot see each other).
- Six composition patterns (route+fill args, select instead of generate, find/judge evidence, turn judgements into reusable data, verify and escalate, respond to changing state) with links to specific cookbooks.
- Primitives table: **Choice** = one of a defined set; **Noul** = probability a condition holds; **Score** = probability-weighted position on ordered levels.
- Guidance on using probabilities vs confidence, validating thresholds on the user's own data, keeping API credentials server-side, and treating cookbook thresholds as examples not universal rules.

**npm / CLI question — IMPORTANT NUANCE:**
- The `skills` CLI **is** published on npm (`https://registry.npmjs.org/skills`) — but it is **not a TypeSafe product**. It is a generic third-party installer: "The open agent skills ecosystem", repo `vercel-labs/skills`, latest **1.7.0 published `2026-09-17T15:02:04Z`**, `bin: {skills, add-skill}`.
- TypeSafe publishes **no** skill/CLI package. Direct registry probes returned **404 Not published** for `@typesafe-ai/skills`, `@typesafe-ai/cli`, `@typesafe-ai/sdk-js`, `@typesafe-ai/mcp`, `typesafe-ai`.
- The `typesafe-ai` GitHub org repo list contains no CLI (`skills`, `typesafe-sdk-js`, `typesafe-sdk-python`, `system-one-adapter-python`, `daggerverse`, `Overwatch`, `pulumi-clickhouse`, `typesafe-ai.github.io`, plus mirrored forks `LLaDA`, `vllm`).

So: **the install command is real and officially documented, but `npx skills` is Vercel's third-party CLI, not something TypeSafe publishes.**

⚠️ **Documentation/repo discrepancy:** [docs.typesafe.ai/agent-skill](https://docs.typesafe.ai/agent-skill) says for manual installation to copy "the entire `skills/typesafe-ai` directory, **including its reference files**". The repo tree shows that directory contains only `SKILL.md` and `LICENSE` — **no reference files exist**. (Recorded as unverifiable/likely stale doc text.)

---

## 2. `AbdelStark/awesome-typesafe` — CONFIRMED

[github.com/AbdelStark/awesome-typesafe](https://github.com/AbdelStark/awesome-typesafe)
- Description: "A curated list of official resources and community projects for TypeSafe, System One models, and Jev."
- **★122** · forks 16 · license MIT · language CSS · created `2026-09-17T06:56:37Z` · pushed `2026-09-18T08:31:44Z`
- Star count was **120** ~30 min earlier the same session, then 122 — i.e. it is rising fast.
- README states: *"Last reviewed: 2026-09-17"* and *"This repository is not affiliated with or endorsed by TypeSafe AI."*
- **Stars per project are NOT shown** anywhere in the README (no star counts, no tables). 40 unique GitHub repo URLs are referenced; 24 links in the official section, ~41 entries in the community section (some are non-repo demos/blog/X posts).

### Full indexed list

**Official resources (24 links)** — product site, docs, HTTP API, demos, evals; **SDKs/tools:** [JS SDK](https://github.com/typesafe-ai/typesafe-sdk-js), [Python SDK](https://github.com/typesafe-ai/typesafe-sdk-python), [System One Adapter](https://github.com/typesafe-ai/system-one-adapter-python), [Agent Skills](https://github.com/typesafe-ai/skills), TypeSafe org; concepts (primitives, confidence, patterns, use-case map, cookbooks, agent-skill guide); research (launch post, manifesto, "The Bitterest Lesson", "AI: too good to be true…"); community (Discord, X, LinkedIn).

**Community — Client libraries and integrations**
| Project | Purpose | URL |
|---|---|---|
| Advocaat | Small TS client with tagged helpers for typed chances/choices/scores | github.com/pithings/advocaat |
| HA-Jev | Home Assistant integration turning typed questions into sensors/automations; token budget halts evaluation; no explanations, not for safety decisions | github.com/AboveColin/HA-Jev |
| pi-typesafe | Pi extension/library: one consented, key-managed client + batched `typesafe_evaluate` tool | github.com/DevMortimer/pi-typesafe |
| RubyLLM TypeSafe | TypeSafe provider for RubyLLM 2 with offline model metadata | github.com/kieranklaassen/ruby_llm-typesafe |
| s1-rs | Rust derive layer for Choice/Score/Noul + network-free testing | github.com/AbdelStark/s1-rs |
| TypeSafe AI for Rust | Rust client, async + blocking transports, observable retries | github.com/Twister915/typesafe-ai |
| typesafe-ai-rails | Rails integration on typesafe-sdk with usage/cost telemetry | github.com/GenieRobot/typesafe-ai-rails |
| typesafe-rs | Latency-focused Rust transport SDK, parity with official clients | github.com/AbdelStark/typesafe-rs |
| typesafe_sdk | Elixir SDK w/ typed Choice/Score/Noul structs | github.com/nshkrdotcom/typesafe_sdk |
| typesafe-sdk | Ruby client, thread-safe pooled HTTP, Ruby 3.1+ | github.com/joshmn/typesafe-sdk |
| TypeSafeAI.Net | .NET client + Microsoft.Extensions.AI adapters | github.com/Hawxy/TypeSafeAI.Net |
| Vercel AI Gateway | Third-party gateway entry for calling Jev | vercel.com/ai-gateway/models/jev *(non-repo)* |

**Community — Agent and developer tooling**
| Project | Purpose | URL |
|---|---|---|
| Bicameral | Pi harness: LLM writes, Jev supplies typed reflexes; explicitly not a sandbox | github.com/AbdelStark/bicameral |
| Every | Semantic code search CLI asking yes/no of every function | github.com/sufianetaouil/every |
| Jev MCP | Python MCP server exposing classify, score, check, match, screen | github.com/blakestone-x/jev-mcp |
| **Jev Review** *(in known list)* | Staged code-review workflow + local dashboard | github.com/devagrawal09/jev-review |
| jev-axi | CLI for blocking risky tool calls, prompt-injection screening, log triage, diff flagging, ranking | github.com/shiftynick/jev-axi |
| jev-mobile | Experimental Android agent, per-step choices over prevalidated actions | github.com/Friedjof/jev-mobile |
| jevcal | Fits per-question confidence thresholds on labeled data, CI re-check | github.com/abhixhek/jevcal |
| pi-jev | Pi extension: shadow-mode gate, output judge, `jev_ask` | github.com/y0usaf/pi-jev |
| pi-warden | Pi guardrails, held tool result / short steer | github.com/DevMortimer/pi-warden |
| Supercov | Jev scores each source file so agent knows what to fix first | github.com/supercorp-ai/supercov |
| TypeSafe MCP | Go CLI + single-binary MCP server | github.com/itsmostafa/typesafe-mcp |

**Community — Browser agents**
| Project | Purpose | URL |
|---|---|---|
| Jev Browser | Agent skill/runtime; Jev selects browser actions in an observation-action-verification loop | github.com/vlad-terin/jev-browser |
| **Jev Ultrafast** *(known list)* | Browser Use agent, dynamic indexed action space, measured Google Flights demo | github.com/browser-use/jev-ultrafast |

**Community — Games, robotics, interactive demos**
| Project | Purpose | URL |
|---|---|---|
| Crowdcheck | Live demo: 144-char post vs 10,000 synthetic personas | crowdcheck-ai.vercel.app *(non-repo)* |
| HEIST//ONE | Browser stealth game; 6 guards, code owns simulation | github.com/AbdelStark/heist-one |
| **Jev Drone** *(known list)* | MuJoCo quadrotor, control/safety in code, Jev for tactical judgements | github.com/RomanSlack/jev-drone |
| Jev Plays Pokémon | FireRed/Showdown harness, picks move or switch | github.com/anxkhn/JevPlaysPokemon |
| Jev Plays StarCraft | Structured-state harness + probability trace | github.com/phyous/tsai-sc |
| **Jev Search** *(known list)* | Source/time-range/query selection + ranking via Search1API | github.com/superagents-lab/jev-search |
| **TypeSafe Mario** *(known list)* | NES controller: emulator telemetry → structured state → legal actions | github.com/fhshaik/typesafe-mario |
| TypeSafe Typewriter | Live Val Town demo, 16 typed judgements as text changes | typesafe-demo.val.run *(non-repo)* |

**Community — Evaluations and independent research**
| Project | Purpose | URL |
|---|---|---|
| calibre | Calibration measurement on Banking77 + Web of Science; frozen protocol; no routing parameter transferred between datasets | github.com/FirasSX914/calibre |
| Jev Judge vs Dimension Scores | 1 direct question vs 12–14 scored dimensions, 5,477 rows / 34.1M tokens / $1.43 | agentjournal.dev/blog/llm-judge-vs-feature-extraction *(non-repo)* |
| Jev Rerank Bench | Reranking comparison w/ raw responses + uncertainty intervals | github.com/anessbelbati/jev-rerank-bench |
| Jev Spam Eval | Zero-shot spam study vs TF-IDF, post-hoc-tuning caveats | github.com/bitnovus/jev-spam-eval |
| OpenJev | Open-model research baseline for direct typed option scoring; reproduces interface, not the model | github.com/TheoLeeCJ/openjev |
| TypeSafe AI Benchmark | Jev vs Qwen-on-Cerebras, raw exports + cost accounting | github.com/iammrduncan/typesafe-ai-benchmark |

**Community — Showcases and field notes** (all non-repo): Browser Use + Jev (X/@gregpr07), Internal classifier field note (X/@identityTorn), Jev Typewriter launch post (X/@stevekrouse), Qwen on Cerebras comparison (X/@iamMrDuncan), "Typed Decisions, Not Chat" (warmersun.com/jev/).

### Gap analysis vs the known list
Of the 13 repos in the supplied known list, **only 5 are indexed** by awesome-typesafe:

| Known-list repo | In awesome-typesafe? | Exists on GitHub? |
|---|---|---|
| browser-use/jev-ultrafast | ✅ IN LIST | ★3533 Python |
| fhshaik/typesafe-mario | ✅ IN LIST | ★243 Python |
| devagrawal09/jev-review | ✅ IN LIST | ★208 TypeScript |
| RomanSlack/jev-drone | ✅ IN LIST | ★55 Python |
| superagents-lab/jev-search | ✅ IN LIST | ★8 TypeScript |
| tamaratran/fast-jev-compaction | ❌ NOT IN LIST | ★1841 TypeScript |
| jarrodwatts/jev-trader | ❌ NOT IN LIST | ★671 TypeScript |
| thruwire/foreman | ❌ NOT IN LIST | ★239 Python |
| ekzhang/openjev-sglang | ❌ NOT IN LIST | ★92 Python |
| ChetasLua/jevmeter | ❌ NOT IN LIST | ★46 Python |
| lomeshdutta/skill-router | ❌ NOT IN LIST | ★2 Python |
| Heman10x-NGU/Verdict-open-jev | ❌ NOT IN LIST | ★1 Python |
| stephanj/parallelConstraintDecoding | ❌ NOT IN LIST | ★5 Java |

**All 8 absent repos do exist** — so this is a curation gap in the awesome list, not missing projects. Notably the #1 and #2 starred projects in the known list (`fast-jev-compaction`, `jev-trader`) are not indexed.

---

## 3. New Jev repos with real code (created/updated since ~2026-09-17 09:00Z)

Verified by fetching each repo's recursive file tree and README — **all entries below have real source files, not README-only**. GitHub descriptions are quoted only where corroborated by the README/tree.

**Most substantive:**

| Repo | ★ | Lang | Created / pushed | Files (code) | What the code actually does |
|---|---|---|---|---|---|
| [jkudish/jev-mcp](https://github.com/jkudish/jev-mcp) | 56 | TS | 09-17T02:25Z / 09-18T08:52Z | 17 (3) | MCP server exposing `jev_verify`, `jev_screen`, `jev_find`; ~150–500 ms/call. npm `@jkudish/jev-mcp` **0.3.0** (2026-09-18T05:02:55Z). |
| [jkudish/jev-browser](https://github.com/jkudish/jev-browser) | 36 | TS | 09-17T19:22Z / 09-18T08:36Z | 35 (7) | Browser agent as MCP server/CLI/library; Playwright Chromium; Jev picks one action per step and scores goal-met/stuck. npm `@jkudish/jev-browser` **0.3.0**. |
| [bnsd55/jevmlx](https://github.com/bnsd55/jevmlx) | 15 | Python | 09-17T10:20Z / 09-18T08:12Z | 100 (62) | Local MLX on Apple Silicon: scores every allowed answer of a bool/enum/multi-select schema in **one batched forward pass**, assembles JSON in code. `jevmlx decide --preset fintech_fraud`. |
| [ekzhang/openjev-sglang](https://github.com/ekzhang/openjev-sglang) | 92 | Python | 09-17T18:11Z / 09-18T06:41Z | 78 (34) | Implements the TypeSafe/Jev HTTP API on **Qwen3.6-35B-A3B via SGLang** (B200, rust frontend, radix caching, breakable prefill CUDA graphs); Modal deploy. |
| [saibimajdi/typesafeai-dotnet-sdk](https://github.com/saibimajdi/typesafeai-dotnet-sdk) | 5 | C# | 09-16T19:18Z / 09-18T03:13Z | 138 (77) | Community .NET SDK (NuGet `TypeSafeAI.Sdk`), typed noul/choice/score, explicitly "not affiliated with TypeSafe AI". |
| [kikoncuo/jevfire](https://github.com/kikoncuo/jevfire) | 4 | JS/Py | 09-16T14:45Z / 09-18T08:47Z | 280 (105) | JEV/RLCD-inspired **parallel constrained decoding** for CUDA+vLLM: scores verified single-token labels with the pretrained LM head, maps winners to allowed values, JSON assembled in code. Browser Mario example ~71 ms/action. |
| [ohernandezdev/jevmod](https://github.com/ohernandezdev/jevmod) | 0 | Python | 09-17T14:19Z / 09-18T08:56Z | 142 (64) | Moderation: per-message probabilities for spam/scam/harassment/nsfw/off-topic/self-harm/doxxing/CSAM + plain-English rules; Discord/Telegram/Reddit bots, CLI, Python, npm, HTTP API, MCP. Claims ~$0.04/1k messages. |
| [brnyxx/jev-ra](https://github.com/brnyxx/jev-ra) | 0 | Python | 09-18T02:44Z / 09-18T08:41Z | 215 (89) | Browser-use layer for CLI coding agents (MCP + CLI); Jev picks operation **and** target element per step. README benchmark table claims 7.5–8.5× faster than browser-use + gemini-3-flash. |
| [Heman10x-NGU/Verdict-open-jev](https://github.com/Heman10x-NGU/Verdict-open-jev) | 1 | Python | 09-17T18:01Z / 09-18T06:17Z | 145 (53) | Non-autoregressive decision engine on **ModernBERT-151M** with RLCD calibration; HF model `heman10x/rlcd-modernbert-151m`, in-browser WebGPU playground; "inspired by" Jev, not official. |
| [m0rphtail/triagedy](https://github.com/m0rphtail/triagedy) | 0 | Rust | 09-18T06:54Z / 09-18T08:48Z | 29 (18) | Security alert triage as a **UNIX filter**: JSONL alerts in, typed decisions out; Jev or a local model; policy routing stays in code. |
| [alexbejan/jevkit](https://github.com/alexbejan/jevkit) | 0 | Python | 09-17T20:26Z / 09-18T08:51Z | 31 (21) | Jev as a bounded judgement layer for computer use (Cua Driver desktop, phone-harness); Jev never acts or invents coordinates. |
| [ChetasLua/jevmeter](https://github.com/ChetasLua/jevmeter) *(known list)* | 46 | Python | 09-17T11:39Z / 09-17T12:36Z | 42 (15) | Scores every sentence of a video and renders a 16:9 edit; `install.sh`, presets, eval results. |
| [tamaratran/fast-jev-compaction](https://github.com/tamaratran/fast-jev-compaction) *(known list)* | 1841 | TS | 09-17T05:57Z / 09-18T04:45Z | 26 (14) | Claude Code plugin replacing the compaction summary with Jev decisions; hooks + tests. |
| [thruwire/foreman](https://github.com/thruwire/foreman) *(known list)* | 239 | Python | 09-17T11:46Z / 09-17T12:32Z | 41 (31) | "Software Factory Foreman" with src/ + tests. |
| [lomeshdutta/skill-router](https://github.com/lomeshdutta/skill-router) *(known list)* | 2 | Python | 09-18T04:11Z / 09-18T05:29Z | 36 (13) | Picks which installed Claude Code skill a session needs: lists installed skills, asks Jev to rank them, escalates to skills.sh when none fits. |

**Additional real-code repos within the window (verified trees):** [qddegtya/qualm](https://github.com/qddegtya/qualm) ★1 TS — typed decisions where `unsure` is a distinct compiler-enforced branch (src/, tests, CI); [Nasrallah-AL/jev-cli](https://github.com/Nasrallah-AL/jev-cli) ★1 TS — npm **`jevctl` 0.1.0** (2026-09-18T08:51:58Z), commands `jev verify/screen/find/ask`, plus a Claude Code plugin; [Spykoninho/trading-bot-jev](https://github.com/Spykoninho/trading-bot-jev) ★0 TS — Binance-testnet paper trading, Jev judges news, README itself notes the strategy loses after 0.1% fees; [raihankhan-rk/jevarena](https://github.com/raihankhan-rk/jevarena) ★0 TS — two Jev agents race to claim clickable DOM elements; [xingwudao/OpenJev](https://github.com/xingwudao/OpenJev) ★0 Python — Jev-inspired API with **local mock server, synthetic probabilities**, Python+TS SDKs; [maker-KK/todo-jev](https://github.com/maker-KK/todo-jev) ★0 Python — task classifier + 3-tier routing; [felixfisher/pi-jev-compaction](https://github.com/felixfisher/pi-jev-compaction) ★0 TS — Pi extension, **disabled by default** (`enabled: false`); [IgorWarzocha/jev-plays-balatro](https://github.com/IgorWarzocha/jev-plays-balatro) ★0 Python — Balatro mod + controller that **explicitly documents failure** ("Experiment complete. No winning run was demonstrated", best run reached ante 8 Big Blind); [FirasSX914/Janus](https://github.com/FirasSX914/Janus) ★2 Python — calibration + confidence routing on Banking77/Web of Science; [fatwang2/jev-review-action](https://github.com/fatwang2/jev-review-action) ★0 JS — GitHub submission review/PR classification; [memovai/openevals](https://github.com/memovai/openevals) ★0 TS; [EdytaKucharska/ticket-quest](https://github.com/EdytaKucharska/ticket-quest) ★0 TS; [kavehmz/typesafe-playground](https://github.com/kavehmz/typesafe-playground) ★0 JS; [nekowasabi/jev-routing-go](https://github.com/nekowasabi/jev-routing-go) ★0 Go; [ourines/hermes-jev](https://github.com/ourines/hermes-jev) ★0 Python; [HomenShum/jev-swap](https://github.com/HomenShum/jev-swap) ★0 Python; [jerryfane/omp-jev-compaction](https://github.com/jerryfane/omp-jev-compaction) ★0 TS; [markfive-proto/typesafe-vs-deepseek](https://github.com/markfive-proto/typesafe-vs-deepseek) ★0 Python; [youshinh/md-memo](https://github.com/youshinh/md-memo) ★0 JS; [qiz029/dscode](https://github.com/qiz029/dscode) ★2 JS.

**Also new: a wave of community SDKs in other languages** (all created/pushed 09-17→09-18): `kgonia/typesafe-sdk-java` ★1 Java, `saibimajdi/typesafeai-dotnet-sdk` ★5 C#, `2389-research/typesafe-go` ★2, `Stumble/jev-go` ★1, `Shubham510/typesafe-go` ★0, `FelineStateMachine/typesafe-go` ★0, `kazz187/jev-sdk-go` ★0, `zhirschtritt/typesafe-go` ★0, `rocktavious/typesafe-sdk-go` ★0, `latere-ai/typesafe-ai-go-sdk` ★1, `SergeAx/typesafe-sdk-go` ★0, `ainame/swift-typesafe` ★2, `InsaneArts/typesafe-sdk-swift` ★2, `abeldzan/jev-rs` ★0, `netf/typesafe-sdk-rs` ★0, `aoprisan/typesafe-ai-rust-sdk` ★0, `aoprisan/typesafe-ai-scala-sdk` ★0, `nshkrdotcom/typesafe_sdk` ★1 Elixir, `vinnie357/typesafe_sdk_ex` ★0, `Biztactix-Ryan/TypeSafe.Sdk.C-` ★0.

**Observation (factual, not speculation):** there are **at least seven near-identical curated lists** created in the same window — `AbdelStark/awesome-typesafe` (★122), `AnotiaWang/awesome-jev` (★39), `SeeAPI/awesome-jev-use-cases` (★3), `FirasSX914/…`, plus `MrJev/awesome-jev` (★1), `anandi1989/awesome-jev-usecases` (★1), `rhc98/awesome-jev` (★1), `yzfly/awesome-jev-zh` (★1), `fatwang2/awesome-jev` (★1), `OmniJev/awesome-jev` (★1). Most are README-only and several claim to be "curated by Jev itself" (e.g. `rhc98/awesome-jev`'s description). Treat list contents as unvetted.

---

## 4. Official SDK packages — CONFIRMED

### Python — `typesafe-sdk` (PyPI)
[source: pypi.org/pypi/typesafe-sdk/json](https://pypi.org/pypi/typesafe-sdk/json)
- **Latest version 0.6.0**, uploaded **`2026-09-15T10:23:18Z`** (wheel + sdist)
- `requires_python: >=3.10`; summary "Python SDK for TypeSafe AI API."
- Repo: `https://github.com/typesafe-ai/typesafe-sdk-python` (★65) · Docs: docs.typesafe.ai/sdk/python
- Release history: `0.0.1a0` (2026-09-09T10:34Z) → `0.5.7` (2026-09-11T23:05Z) → **`0.6.0`** (2026-09-15T10:23Z)
- Install: `pip install typesafe-sdk` or `uv add typesafe-sdk`; env `TYPESAFE_API_KEY`

**Core API surface** (from `src/typesafe_sdk/__init__.py` `__all__`, read directly):
- Clients: `TypeSafeClient` (sync), `AsyncTypeSafeClient` (async), `Models`, `AsyncModels`; `RetryPolicy`; `__version__`
- Question constructors: `Choice` / `ChoiceModel`, `Noul` / `NoulModel` / `NoulCriteria`, `Score` / `ScoreModel`, `Question`, `QuestionModel`, `Questions`
- Method: `client.system_one(state=..., questions={...})`
- Response types: `SystemOneResponse` with `.nouls`, `.choices`, `.scores`; `Answer`, `ChoiceAnswer`, `NoulAnswer`, `ScoreAnswer`, `ListModelsResponse`, `ModelMetadata`, `Usage`
- Errors: `TypeSafeError`, `TypeSafeAPIError`, `TypeSafeAPIConnectionError`, `TypeSafeAPITimeoutError`, `TypeSafeAPIResponseValidationError`, `TypeSafeAuthenticationError`, `TypeSafeBadRequestError`, `TypeSafeNotFoundError`, `TypeSafePermissionDeniedError`, `TypeSafeRateLimitError`, `TypeSafeUnprocessableEntityError`, `TypeSafeInternalServerError`
- Types: `JSONValue`, `JSONContent`

### JavaScript/TypeScript — `@typesafe-ai/sdk` (npm)
[source: registry.npmjs.org/@typesafe-ai/sdk](https://registry.npmjs.org/@typesafe-ai%2Fsdk)
- **Latest version 0.6.0**, published **`2026-09-15T18:17:19Z`**; dist-tags `{latest: 0.6.0, bootstrap: 0.0.0-bootstrap.0}`
- Description "TypeScript SDK for the TypeSafe API"; repo `github.com/typesafe-ai/typesafe-sdk-js` (★97); zero runtime dependencies; ESM + CJS + `.d.mts`/`.d.cts` declarations
- Release history: `0.0.0-bootstrap.0` (2026-09-12T02:56Z) → `0.5.7` (2026-09-12T04:13Z) → **`0.6.0`** (2026-09-15T18:17Z)
- Install: `npm install @typesafe-ai/sdk` (Node.js 20+)

**Core API surface** (from `src/index.ts` exports, read directly):
- `TypeSafeClient` with `client.systemOne({ state, questions })`
- Question helpers: `choice()`, `noul()`, `score()` (lowercase)
- Response access: `response.answers.<questionId>.choice` (answer types inferred from the questions)
- Also exported: `APIPromise`, `WithResponse`, `ENV`/`EnvVar`, `LOG_LEVELS`, `Models`, `VERSION`, and all types

### Related official package
- `typesafe-ai/system-one-adapter-python` (★96, Python, pushed 2026-09-16T22:55:36Z) — drop-in `TypeSafeClient` replacement backed by OpenAI/Anthropic/OpenAI-compatible LLM APIs.

⚠️ **Trap:** an unrelated npm package named `typesafe-sdk` exists at version `0.0.0` (published 2026-09-16T21:13:50Z, no repository field). That is **not** the official Python package and **not** the official JS SDK — the official JS package is the scoped `@typesafe-ai/sdk`.

---

## 未能核实 (could not verify)

1. **End-to-end execution of `npx skills add typesafe-ai/skills --skill typesafe-ai`.** I confirmed the command is documented in two official places and that the `skills` CLI exists on npm, but I did **not** run the installer, so actual installation success, the skills.sh registry entry for this repo, and the resulting on-disk layout are unverified.
2. **The "reference files" referenced by docs.typesafe.ai/agent-skill.** The docs say to copy the `skills/typesafe-ai` directory "including its reference files", but the repo tree contains only `SKILL.md` + `LICENSE`. I could not find any reference files — recorded as a documentation/repo discrepancy.
3. **Per-project star counts in `awesome-typesafe`.** The README shows **no** star counts for indexed projects; the 40 repo URLs were extracted, and stars were only obtainable by separately querying the GitHub API. Star figures in item 2's gap table are my own API measurements, not from the list.
4. **All performance/accuracy/cost claims made inside READMEs** (e.g. jev-ra's 7.5–8.5× speedup, jevmeter's "99% held-out", jev-mcp's 150–500 ms, jevmod's $0.04/1k messages, calibre/Verdict numbers). I verified that real code exists; I did **not** reproduce or audit any benchmark.
5. **The public launch date "2026-09-15/16".** Not verified from a TypeSafe primary source in this pass. The only statement seen is third-party: `AnotiaWang/awesome-jev` README says *"Jev launched in early access on 15 September 2026."* The `typesafe.ai` launch blog was not fetched.
6. **Whether any item-3 repo is official.** None of them appear in the `typesafe-ai` org repo list, and several explicitly disclaim affiliation — but I only enumerated the org's public repos (11), so a private/unlisted official repo cannot be excluded.
7. **`web_fetch` could not be used at all for GitHub/raw.githubusercontent.com** in this environment (DNS override to non-public `198.18.0.15`). All GitHub evidence came from `curl` + authenticated `gh api`. Non-GitHub sources (PyPI, npm, docs.typesafe.ai) were fetched normally.
8. **awesome-typesafe's GitHub Pages "live site"** (`abdelstark.github.io/awesome-typesafe/`) was not fetched — only the repo README.
9. **`@jkudish/jev-mcp` / `@jkudish/jev-browser` package contents** were confirmed to exist on npm (0.3.0 each) but their tarballs were not downloaded/inspected.

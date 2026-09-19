# Jev Lab — TypeSafe System One Model Research & Benchmarks

> **A hands-on research lab for [Jev](https://typesafe.ai) (TypeSafe's System One model)** — structured decisions, not text. We test Noul / Choice / Score primitives on real business problems (support-ticket routing, agent control, confidence gates), verify community claims with reproducible experiments, and track the ecosystem day by day.

[![Tests](https://img.shields.io/badge/tests-38%20passed-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![Model](https://img.shields.io/badge/model-jev--1.13.0-blueviolet)](https://docs.typesafe.ai/models)
[![Zero deps](https://img.shields.io/badge/deps-stdlib%20only-orange)](scripts/)

---

## TL;DR — what we found

Jev is a **System One model**: you send a `state` + typed questions, it returns typed answers with probabilities (Noul = yes/no, Choice = pick from options, Score = ordered rubric). No text generation — which makes it **cheap, fast, and non-hallucinating by construction** (schematically, not semantically).

Our measured highlights (all reproducible in this repo):

| Claim | Our data | Evidence |
| --- | --- | --- |
| Multi-question fan-out is free | 1 → 20 Noul questions: **P50 ≈ 1.4s, no latency growth** | [`docs/jev-validation-2026-09-18.md`](docs/jev-validation-2026-09-18.md) |
| Cost is tiny | 108 requests ≈ **$0.0044** total | same report |
| Decisions are repeatable | 3 runs × 36 tickets: **100% decision agreement** | [`artifacts/`](artifacts/) |
| `confidence` beats argmax for gating | On failures: confidence 0.04–0.16 vs top-1 prob 0.58 — **use confidence, not argmax** | [`docs/jev-round3-2026-09-18.md`](docs/jev-round3-2026-09-18.md) |
| Keyword baseline beat Jev on our pilot data | 97.2% vs 91.7% — **pilot data was too easy; don't over-trust vendor evals** | validation report |
| End-to-end latency ≈1.5s, not <100ms | Official claim vs our full-path (network + gateway) measurement | validation report |

**Caveat we keep repeating:** probabilities are NOT production accuracy. Calibrate on your own data, pin `jev-1.13.0`, and treat any single Noul below ~0.5 as "unknown", not "no".

## Quick start

1. Copy `.env.example` → `.env` and fill in `TYPESAFE_API_KEY`.
2. Try one call (needs `curl`):

```sh
set -a; . ./.env; set +a
curl --fail-with-body --silent --show-error \
  https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"model":"jev-latest","state":"The customer cannot connect to Wi-Fi before a meeting today.","questions":{"urgent":{"type":"noul","instructions":"Does this message express urgency?"}}}'
```

3. Run the offline unit tests (no key needed):

```sh
python3 -m unittest discover -s tests   # 38 tests, stdlib only
```

## What's inside

```
docs/       6 research rounds — validation, ecosystem, official-claim audit, community cases
evals/      6 datasets — support routing, agent control, confidence escalation, thinking supervision
scripts/    9 reproducible eval & compare scripts (pure stdlib, no SDK)
artifacts/  raw JSON + generated reports, incl. repeat-stability across runs
tests/      38 unit tests, runnable offline
```

## Research log — highlights

| Doc | Round | Content |
| --- | --- | --- |
| [**Validation**](docs/jev-validation-2026-09-18.md) | 1st | Support-ticket routing benchmark (108 calls), fan-out latency, cost, repeat-stability, keyword baseline, agent-control (context filtering / pathfinding / model routing) |
| [**Thinking supervision**](docs/jev-thinking-supervision-2026-09-18.md) | 2nd | Observing + interrupting the reasoning window via a third-party gateway (mechanism experiment — did not shorten answers) |
| [**Round 3**](docs/jev-round3-2026-09-18.md) | 3rd | Official-claim verification, ecosystem index quality, **confidence-escalation gate** (3 runs × 36 probes, 0.6–0.7 threshold passes 91.7% with 100% error capture) |
| [**Round 4**](docs/jev-round4-2026-09-19.md) | 4th | Independent third-party benchmarks, TechCrunch coverage, open-source System One (CUA-S1), ecosystem risks |
| [**Round 4 · supplement**](docs/jev-round4-supplement-2026-09-19.md) | 4th | Official doc deltas (Language support / Patterns / evals table), $40M funding facts, Vercel / LangChain / OpenRouter integration, the "13% adoption" asterisk, Jev-driven browser cases, Theo's context-compaction criticism |
| [**Round 5**](docs/jev-round5-2026-09-19.md) | 5th | Who is actually using Jev: medical screening, DevOps, ERP, content scoring, PR review, voice control — and the honest gap: "everyone ran it once, nobody has been on duty for 30 days" |
| [**Round 5 · supplement**](docs/jev-round5-supplement-2026-09-19.md) | 5th | 28-case community audit against GeekCat's list — 14 missed cases recovered (realtime assistance, SQL/vector search, code quality gates) |
| [**Community survey**](docs/jev-x-use-cases-2026-09-18.md) | survey | X / GitHub usage index, risks, selection criteria |

Raw data → `artifacts/`, datasets → `evals/`, scripts → `scripts/`.

## Reproduce the benchmarks

```sh
# support-routing benchmark (3 rounds) + keyword baseline
python3 scripts/evaluate_support.py --run-name support-routing-v1
python3 scripts/evaluate_keyword_baseline.py

# fan-out latency (1→20 parallel questions)
python3 scripts/benchmark_fanout.py

# confidence escalation gate (needs API key)
python3 scripts/evaluate_confidence_escalation.py
```

## Key lessons (so you don't have to learn them)

1. **Fan-out is the killer feature** — ask many questions per request; latency barely moves, cost stays in the sub-cent range.
2. **`confidence` ≠ argmax probability** — on our failing cases they differed by an order of magnitude. Gate on `confidence`.
3. **Pin the version** — aliases move; log the `model` field from every response (`jev-1.13.0` as of 2026-09-19).
4. **CJK is officially weaker** — "handled but not equally well"; test Chinese before trusting it.
5. **Vendor evals are self-evaluations** — labels generated by other models (GPT-6 Astra + Claude Fable 5.1), no human labeling. Our "facts-checkable" probes are the contrast.
6. **Compaction / routing that rewrites context breaks LLM prompt caches** (community-measured: 99.35% → 32% hit rate) — keep deletions recoverable, keep numbers in code.

## Roadmap / next

- [ ] Chinese & mixed CN-EN ticket probes (official docs flag CJK as weaker)
- [ ] Latency breakdown (DNS/TLS/gateway vs model) to explain the 1.5s vs 176ms gap
- [ ] Re-run with official SDK instead of raw `urllib`
- [ ] Escalation cascade: Jev first pass → strong model only when uncertain
- [ ] Watch post-Sept-25 pricing / retention on Vercel AI Gateway

## License & disclaimer

Repo is research material: **do not treat single-run probabilities as production accuracy or as permission to auto-execute.** API pricing/versions are from official docs at capture time (2026-09-19). See each report for its evidence level (verified structure / vendor-reported / author-reported).

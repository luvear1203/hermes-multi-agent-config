---
title: Cost Tiers — capability-based cost tier system + hardware roadmap
created: 2026-05-04
updated: 2026-05-10
type: architecture
tags: [multi-agent, cost, hardware, model]
sources:
  - https://lmarena.ai
  - https://livebench.ai
  - https://aider.chat/docs/leaderboards/
  - https://www.swebench.com/
confidence: medium
---

# Cost Tiers

Tiers are defined by **capability**, not by model name.
When models change, the tier system stays stable; only the candidate roster updates.

## Classification Criteria

- **Frontier reasoning** — top of public benchmarks (LMArena, LiveBench, Aider Polyglot, SWE-bench, GPQA) + strong real-world reviews (Reddit/HN/X)
- **Strong but cost-aware** — just below Frontier, excellent cost-efficiency
- **Local open-weight, capable enough for repetition** — runs locally, sufficient for simple repetitive/mechanical tasks
- **Non-LLM automation** — scripts · CI · quantitative checks

## Tier Definitions and Candidate Roster (as of 2026-05-10)

### Tier 1 — Frontier Reasoning
Target roles: Director, Sub-Director, Engine Architect

| Candidate | Call path | Notes |
|---|---|---|
| GPT-5.5 | Hermes `openai-codex` provider (ChatGPT Pro subscription, OAuth), `sub-director` profile | **Sub-Director (re-demoted 2026-05-10)**. Pre/post review path, fallback when Director (Opus 4.7) is rate-limited or contextually mismatched. ChatGPT Pro subscription quota, no per-token billing. |
| **Claude Opus 4.7** | Anthropic OAuth (Max plan), `orchestrator` profile + bypass 5-patch | **Director (re-promoted 2026-05-10)**. Reason: Opus 4.7 출력 품질 우선. Default `hermes chat` and `hermes chat --profile orchestrator` route through Anthropic Max OAuth. Reasoning effort `medium` (Opus는 medium/high만). |
| Claude Sonnet 4.6 | Anthropic OAuth | candidate for delegate_task workers; not for direct hermes chat (long-context tier triggers 429) |
| Claude Haiku 4.5 | Anthropic OAuth (Max plan), `dev-gemma` profile | **Code Implementation worker (assigned 2026-05-10)** — replaced gemma-4-31b-it because Tier 1 paid에서도 16k TPM hard cap이 Hermes 25k 토큰 prompt 수용 못함. Anthropic Max 구독 내 추가 비용 0. 200K context. |
| Gemini 2.x Pro | Google API | candidate |
| DeepSeek V4-Pro | DeepSeek API | may enter Frontier depending on reasoning benchmarks |

### Tier 2 — Strong but Cost-Aware
Target roles: R&D Engineer A·B, Tech Artist

| Candidate | Call path | Notes |
|---|---|---|
| Claude Sonnet 4.6 | Anthropic OAuth (Max) | currently R&D A |
| DeepSeek V4-Pro | DeepSeek API (paid) | currently R&D B |
| **Gemma 4 31B IT** | Google AI Studio API (free tier) | currently **Tech Artist** — 256K input · 32K output · matches Mythrill LLM ② (NL → SI parameter) intent |
| Gemini 2.x Flash | Google API | candidate |
| GLM 5.1 | NVIDIA NIM (free) or Z.ai API | candidate |
| GLM 4.6 | API or local | candidate |

### Tier 3 — Local Open-Weight
Target roles: Engine Programmer assist, Validator script generation, labeling/cleanup

| Candidate | Size | Hardware requirement |
|---|---|---|
| Qwen3 Coder 32B (tentative) | 32B | RTX 5090 quantized |
| DeepSeek-Coder | 33B | RTX 5090 quantized |
| Gemma 4 (planned) | TBD | M1 / RTX |
| Qwen3 235B MoE | 235B | Mac Studio or compact inference PC |

### Tier 4 — Non-LLM Automation
- pytest, regression runner
- graphify indexing
- git/CI

## Roster Update Policy

- Update the table when new bench results or new models ship
- Replace immediately when reinforced Sonnet/Opus versions ship + update harness prompts per [[model-prompting-conventions]]
- Roster updates require sources (bench URL, evaluation post)

## Hardware Roadmap

| Stage | Hardware | Unlocks |
|---|---|---|
| Current | MacBook M1 Air | All roles → paid API. No local LLM |
| Stage 1 | + RTX 5090 + AMD 9950X3D2 desktop | Tier 3 fully local. Validator scripts run local |
| Stage 2 | + Mac Studio or NVIDIA DGX Spark / compact inference PC | Some of Tier 2 local (200B–400B MoE quantized) |
| Final | Two workstations operating | Only Tier 1 paid; rest near-zero cost |

## API Cost-Reduction Principles

- Frontier calls only for Director · Engine Architect critical decisions
- Simple repetition · doc conversion · labeling go local-first
- Debates (researcher-debate) don't need both models at Frontier — heterogeneous distribution is more valuable

## Related Docs

- [[roles]] · [[grand-engine-vision]] · [[model-prompting-conventions]] · [[validators]]

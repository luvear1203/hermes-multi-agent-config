---
title: Studio Roles — English-style role table
created: 2026-05-04
updated: 2026-05-10
type: architecture
tags: [multi-agent, orchestration, architecture]
sources:
  - https://www.fromsoftware-recruit.jp/career/occupation/
  - https://www.epicgames.com/site/en-US/careers/jobs
  - https://www.youtube.com/watch?v=nJfqO5edMFk
confidence: medium
---

# Studio Roles

Multi-agent studio role table for advancing [[grand-engine-vision]].
Reference: union of FromSoftware (auteur vision line) + Epic Games (engine R&D line).

## Role names are English-style

Standardize on English-style titles instead of Korean/Japanese ranks. New roles also use English-style first.

## Role Table

| Role | Analogy | Responsibility | Current Assignment |
|---|---|---|---|
| **Director** | Miyazaki, CEO | Receive vision · plan · final approval | `claude-opus-4-7` via Anthropic Max OAuth (`anthropic` provider, claude_code OAuth in `~/.hermes/auth.json` + `profiles/orchestrator/auth.json` + bypass 5-patch). **Re-promoted 2026-05-10**. Reason: Opus 4.7 출력 품질 우선 (directing 판단 품질 최우선). Sub-Director 강등은 Codex 한도/맥락 mismatch 시 fallback 호출만. Default `hermes chat` and `hermes chat --profile orchestrator` route through Anthropic Max OAuth. |
| **Sub-Director** | Tanimura | Pre-execution plan review, post-completion code/pipeline review, debate moderation | `gpt-5.5` via Codex OAuth, fixed in the `sub-director` profile. **Re-demoted 2026-05-10** from Director. Call: `hermes chat --profile sub-director -q '<review prompt>'`. |
| **Engine Architect** | Epic Principal/CTO | Long-term tech consistency, integrated engine absorption tracking | Frontier reasoning LLM (may double as Director for now) |
| **R&D Engineer A** | Epic R&D | Papers · prior work · evidence collection | Frontier or Strong tier (currently `claude-sonnet-4-5-20250929` via `researcher` profile, default; sonnet-4-6 only via `-m` for explicit long-context work) |
| **R&D Engineer B** | Epic R&D | Same role, cross-validation partner | Frontier or Strong tier (currently `deepseek-v4-pro` via `researcher` profile, `--provider deepseek`) |
| **Tech Artist** | Epic Niagara TA | Translate natural language ↔ simulation parameters; bridge design ↔ code | Strong tier (currently **Gemma 4 31B IT** via Google AI Studio API, free tier; previously DeepSeek V4-Pro) |
| **Engine Programmer** | Epic Engine Engineer | Mainline shipping code | Coding-tuned LLM (currently Claude Code / Codex CLI) |
| **Code Implementation (dev-gemma)** | Epic gameplay programmer (junior) | Spec → TDD → commit | `claude-haiku-4-5-20251001` via `dev-gemma` profile (Anthropic Max OAuth, subscription-included) — **swap 2026-05-10** from `gemma-4-31b-it` because Tier 1 paid에서도 16k TPM hard cap이 Hermes 25k 토큰 prompt 수용 못함. Profile name 유지 (코드 위치 보존), 추후 자체 머신 도입 시 로컬 오픈소스 worker로 재교체 |
| **Validator** | QA | Validate artifacts — on-demand pattern | Not an LLM slot, see [[validators]] |
| **Planner / Narrative Director** | FromSoft scenario planner | C-Chasm IP rule review (5 laws, god classification) | Unassigned — Director doubles |

## Communication Convention (Alex AI video insight)

Each role declares the following three in its SOUL.md:

1. **My role** — define in one line
2. **Peer roles** — who you exchange what with
3. **Output contract** — output format (markdown spec, JSON, code, etc.)

Without these three, multi-LLM orchestration efficiency falls below a single large context — that's the video's key conclusion.

## Wiki-First

When any role hits an unknown fact mid-task:
1. **Search wiki** first
2. If absent or session content doesn't link naturally → **session_search prior conversations**
3. Still missing? No guessing — report knowledge gap to Director
4. Director instructs R&D Engineer A·B to debate (researcher-debate skill)
5. After consensus, update wiki, read the page, resume work

## Multi-Project Slots

Each phase of [[grand-engine-vision]] may have a Project Director slot.
Currently the user fills all Project Director roles; LLM delegation possible later.

## Related Docs

- [[grand-engine-vision]] · [[cost-tiers]] · [[model-prompting-conventions]] · [[validators]]
- [[multi-agent-system]]

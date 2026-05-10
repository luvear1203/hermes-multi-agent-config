---
title: Hermes Multi-Agent System
created: 2026-05-03
updated: 2026-05-10
type: entity
tags: [multi-agent, orchestration, agent, framework]
sources:
  - "~/.hermes/config.yaml"
  - "~/.hermes/profiles/orchestrator/config.yaml"
  - "~/.hermes/profiles/sub-director/config.yaml"
  - "~/.hermes/profiles/researcher/config.yaml"
  - "~/.hermes/wiki/architecture/roles.md"
  - "https://www.youtube.com/watch?v=G47mnkGkYwQ"
confidence: high
---

# Hermes Multi-Agent System

Hermes is the current local multi-agent runtime for advancing [[grand-engine-vision]],
[[mythrill-pipeline]], and [[C-Chasm]]. It remains a CLI/runtime layer, while
[[local-agent-control-plane]] is the planned readable dashboard/control plane
above it.

## Current Architecture

```text
User
  -> Local Agent Control Plane (planned dashboard)
       -> Director: Claude Opus 4.7 via Anthropic Max OAuth
       -> Sub-Director: GPT-5.5 via Hermes openai-codex
       -> Researcher A: Claude Sonnet 4.5 via Anthropic Max OAuth
       -> Researcher B: DeepSeek V4-Pro via researcher override
       -> Tech Artist: Gemma 4 31B IT via Google AI Studio
       -> Code Implementation: Claude Haiku 4.5 via dev-gemma (Anthropic Max OAuth, 2026-05-10 swap from gemma-4-31b-it)
       -> Manual/Codex CLI fallback where appropriate
```

The Director path is Anthropic Max OAuth (claude_code keychain + bypass 5-patch),
not a direct Anthropic API pay-per-token path. Codex OAuth is the explicit
Sub-Director profile path. Provider Path Discipline forbids auto-switching to
direct API on either side.

## Active Profiles

| Profile | Model | Provider | Role | Status |
|---|---|---|---|---|
| `default` | `claude-opus-4-7` | `anthropic` | Default chat path | Active (re-promoted 2026-05-10) |
| `orchestrator` | `claude-opus-4-7` | `anthropic` | Director / main orchestration shell | Active (re-promoted 2026-05-10) |
| `sub-director` | `gpt-5.5` | `openai-codex` | Sub-Director review/fallback | Active (re-demoted 2026-05-10) |
| `researcher` | `claude-sonnet-4-5-20250929` | `anthropic` | Researcher A | Active (smoke 2026-05-10 ok) |
| `researcher` override | `deepseek-v4-pro` | `deepseek` | Researcher B | Active (smoke 2026-05-10 ok) |
| `tech-artist` | `gemma-4-31b-it` | `gemini` (GCP project 1) | Mythrill NL-to-parameter bridge | Active (smoke 2026-05-10 ok) |
| `dev-gemma` | `claude-haiku-4-5-20251001` | `anthropic` | Small implementation worker (TDD) | Active (smoke 2026-05-10 ok). 2026-05-10 swap from gemma-4-31b-it: Tier 1 paid에서도 16k TPM hard cap, Hermes prompt 25k 토큰 수용 불가. Profile name 유지, 추후 자체 머신 도입 시 로컬 오픈소스 worker로 재교체 예정 |

## Invocation Policy

Default Director invocation:

```bash
hermes chat -q '<prompt>'
```

Main orchestrator invocation:

```bash
hermes chat --profile orchestrator -q '<prompt>'
```

Sub-Director invocation:

```bash
hermes chat --profile sub-director -q '<review prompt>'
```

Researcher A invocation:

```bash
hermes chat --profile researcher -q '<research prompt>'
```

Researcher B invocation:

```bash
hermes chat --profile researcher --provider deepseek -m deepseek-v4-pro -q '<research prompt>'
```

Do not silently switch from a subscription/OAuth route to a direct API route.
If the configured path fails because of quota, auth, rate limits, or context
limits, stop and ask the user to choose retry, smaller batch, different model,
different provider, or abort.

## Local Control Plane Relationship

Hermes and OpenClaw are terminal-oriented runtimes. The user wants a separate
local dashboard because terminal UIs are not readable enough for long-running
game-development orchestration. The dashboard will not replace Hermes; it will
wrap Hermes/Codex/OpenClaw through adapters and provide mission state, approval
gates, prompt/context previews, run logs, and knowledge write review.

## History

| Date | Change | Result |
|---|---|---|
| 2026-05-10 | Director ↔ Sub-Director re-swap (Opus 4.7 promoted, GPT-5.5 demoted). Reason: Opus 4.7 출력 품질 우선. | OAuth-only, sub-director profile re-uses Codex credential from pre-rebuild backup. Smoke 7/8 passed |
| 2026-05-10 | dev-gemma model swap: gemma-4-31b-it → claude-haiku-4-5-20251001 | Reason: Tier 1 paid에서도 gemma-4-31b TPM 16k hard cap, Hermes 25k 토큰 prompt 1요청 한도 초과. Haiku 4.5는 Anthropic Max OAuth 구독 내 (추가 비용 0). Profile name `dev-gemma` 유지. Smoke 8/8 GREEN |
| 2026-05-07d | Created `sub-director` profile fixed to Claude Opus 4.7 via Anthropic Max OAuth | Profile exists; runtime verification deferred because Opus/Sonnet subscription quota is exhausted |
| 2026-05-07c | Switched default and `orchestrator` profile to `gpt-5.5` via `openai-codex` | Verified with `hermes status`, default chat, and orchestrator chat |
| 2026-05-07b | Promoted GPT-5.5 to Director, demoted Opus to Sub-Director | Role table updated |
| 2026-05-04 | Opus 4.7 Max OAuth bypass validated | Hermes Claude Max integration usable when quota is available |
| 2026-05-03 | Initial Opus/Sonnet Max OAuth attempts without bypass | Server-side verification blocked higher Anthropic models |

## Key Files

- `~/.hermes/config.yaml` — global default model/provider
- `~/.hermes/profiles/*/config.yaml` — profile model/provider settings
- `~/.hermes/profiles/*/SOUL.md` — role prompts
- `~/.hermes/wiki/architecture/roles.md` — canonical role assignment table
- `~/.hermes/wiki/entities/local-agent-control-plane.md` — planned dashboard/control plane
- `~/.hermes/patches/anthropic_billing_bypass.py` — Anthropic OAuth compatibility patch

## Related

- [[local-agent-control-plane]]
- [[roles]]
- [[cost-tiers]]
- [[hermes-max-integration]]
- [[claude-auth-bypass]]
- [[cron-api-monitor]]
- [[discord-gateway]]

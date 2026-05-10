---
title: Local Agent Control Plane
created: 2026-05-07
updated: 2026-05-07
type: entity
tags: [multi-agent, orchestration, agent, automation, project]
sources:
  - "handoff from companion chat, 2026-05-07"
  - "[[multi-agent-system]]"
  - "[[roles]]"
  - "https://www.youtube.com/watch?v=G47mnkGkYwQ"
confidence: high
---

# Local Agent Control Plane

The Local Agent Control Plane is a planned local-only desktop dashboard for
directing multiple AI agents across [[mythrill-pipeline]], [[C-Chasm]], Unreal
/ Unity game production, natural-language VFX generation, personal assistant
workflows, and long-term project knowledge accumulation.

It exists because Hermes and OpenClaw are useful runtimes but terminal-oriented
interfaces are not readable enough for the user's desired workflow.

## Goal

Build a complete local app that manages agent profiles, roles, rules, missions,
approvals, logs, context packs, and knowledge-write review. It should make
multi-agent game-development orchestration visible and controllable without
turning into a fully autonomous unsupervised system.

## Confirmed MVP Scope

MVP 1 is Mission Board first.

Confirmed scope:

- Mission creation, editing, assignment, and status management
- Manual approval before execution
- Prompt and context preview before execution
- Adapter-based execution through Codex CLI, Hermes profiles, and manual entry
- Run logs with stdout, stderr, exit code, prompt snapshot, and command preview
- Result review path after execution
- Knowledge writes held in an approval queue, not saved automatically

Out of MVP scope:

- Fully automatic execution
- Automatic memory writes
- Automatic file-modification approval
- Full MCP integration
- Full OpenClaw orchestration
- Complex graph-memory UI

## Mission State Flow

```text
Backlog -> Ready -> Awaiting Approval -> Running -> Review -> Done
                                      \-> Failed
                                      \-> Blocked
```

State meanings:

- `Backlog` — idea or task candidate
- `Ready` — sufficiently specified and executable
- `Awaiting Approval` — command/prompt/context preview has been generated
- `Running` — adapter execution is in progress
- `Review` — output needs user or reviewer decision
- `Done` — accepted and closed
- `Failed` — execution failed
- `Blocked` — missing quota, permission, information, or design decision

## MVP Adapters

`CodexCliAdapter`:

```bash
codex exec --skip-git-repo-check -m gpt-5.5 '<prompt>'
```

Primary use: Director, architecture, implementation judgement, coding tasks.

`HermesProfileAdapter`:

```bash
hermes chat --profile <profile> -q '<prompt>' --max-turns 1 -t '' -Q
```

Primary use: Hermes-managed profiles such as `sub-director`, `researcher`,
`tech-artist`, and `dev-gemma`. Claude Opus/Sonnet are accessed only through
this profile adapter, not through a direct Anthropic API adapter.

`ManualAdapter`:

```text
No command. The user pastes external results or marks manual work complete.
```

Primary use: external tools, quota-limited periods, human-only decisions, and
work that should not execute automatically.

## Model and Role Division

| Role | Runtime | Intended use |
|---|---|---|
| Codex / GPT-5.5 | `CodexCliAdapter` or Hermes `openai-codex` | Main Director, architecture, final implementation judgement |
| Claude Opus | `HermesProfileAdapter` / `sub-director` | Sub-Director review after quota reset |
| Claude Sonnet | `HermesProfileAdapter` / `researcher` | Research and review after quota reset |
| Gemma 4 31B IT | `HermesProfileAdapter` / `dev-gemma` or `tech-artist` | Small implementation tasks, UI fragments, tests, NL-to-parameter work |
| DeepSeek V4-Pro | `HermesProfileAdapter` / researcher override | Long-document analysis and low-cost alternate review |

## Recommended Technical Direction

Preferred stack:

```text
Tauri + React + TypeScript + SQLite
```

The app should have a local core with:

- mission runner
- adapter manager
- approval gate
- SQLite persistence
- run-log storage
- file/project watchers
- context-pack builder
- knowledge-write inbox

The dashboard should not try to become the reasoning engine. It should own
state, approvals, routing, and visibility. Actual reasoning and execution stay
inside Codex, Hermes profiles, OpenClaw, MCP tools, or manual workflows.

## Deferred Design Topics

These require Sub-Director review after Claude Opus quota resets:

- DB schema
- profile schema
- mission schema
- memory write policy
- project repo initialization
- OpenClaw integration boundary
- MCP integration boundary
- UI information architecture beyond MVP Mission Board

## Related

- [[multi-agent-system]]
- [[roles]]
- [[cost-tiers]]
- [[grand-engine-vision]]
- [[mythrill-pipeline]]
- [[C-Chasm]]

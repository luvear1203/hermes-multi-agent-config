---
title: Orchestrator Protocol — Director-only operational rules
created: 2026-05-06
updated: 2026-05-10
type: architecture
tags: [orchestration, governance, protocol, director]
sources:
  - "[[roles]]"
  - "[[cost-tiers]]"
confidence: high
---

# Orchestrator Protocol

Rules that apply ONLY to the orchestrator-tier roles defined in [[roles]] —
**Director, Sub-Director, Engine Architect**. Worker roles (R&D Engineer A·B,
Tech Artist, Engine Programmer, Validator) do NOT follow this protocol; they
follow their own SOUL.md and the shared rules in `wiki/CLAUDE.md`.

The shared rules in CLAUDE.md (Wiki-First, change-immediately-to-wiki,
AI-to-AI English-only, Provider Path Discipline) still apply to the
orchestrator on top of everything below.

## End-of-Task Reporting

After every task unit ends, the orchestrator MUST append the following two
items to its reply to the user:

1. **Token quota** — verbatim output of `bash ~/.hermes/bin/quota.sh`.
   The helper is model-aware: it reads active `model.provider`,
   `model.default`, and optional `model.base_url` from `~/.hermes/config.yaml`
   and reports that provider/model's account limits. With the current default
   shell this means `anthropic/claude-opus-4-7` Max session(5h)/weekly(7d) quota
   (active since 2026-05-10 re-promotion); Codex session/weekly numbers report
   only when Sub-Director chat is the active context. Do NOT paraphrase or
   recompute timestamps; the script already converts reset times to KST and
   computes time-until-reset.
2. **Feasibility judgement** for the next planned task using the rules in
   the next section.

Estimation is forbidden. If the script fails, state "quota probe failed"
explicitly instead of guessing.

## Feasibility Judgement Rules

Based on the primary/session utilization reported by `quota.sh`:

| Utilization | Status      | Allowed work |
|-------------|-------------|--------------|
| < 50%       | GREEN       | Heavy worker fan-out OK |
| 50–75%      | YELLOW      | Light worker fan-out only (read-only audits, single-file edits) |
| 75–90%      | RED-soft    | Main 1:1 only, no worker spawn |
| > 90%       | RED         | Reads / reports only, defer new tasks until reset |

Hard blockers (any of these → "cannot start"):
- Weekly utilization > 80% — heavy work deferred regardless of session quota.
- Time-until-primary/session reset < 30 min AND primary/session utilization
  > 60% — task may not finish before the throttle wall, do not start

## Provider Decision Discipline (orchestrator-specific extension)

CLAUDE.md already forbids autonomous switching to direct API paths. As
orchestrator the rule is stricter:

- The orchestrator chooses provider/model assignments for new roles, but
  every assignment that introduces a new billing surface (new paid API,
  new subscription, new credit pool) MUST be presented to the user as
  options, never auto-applied.
- Slot reassignment within already-active providers (e.g. moving Tech
  Artist from DeepSeek → Gemma when both keys exist) is allowed without
  re-asking, but MUST be wiki-recorded the same turn (per CLAUDE.md).

## Worker Spawn Discipline

Before invoking `delegate_task`:

1. Confirm the chosen worker model is compatible with the task type
   (long-context limits, tool requirements). For Sonnet 4.6 via Max OAuth,
   long-context is disabled; keep prompts under ~200K tokens.
2. Write the worker `goal` and `context` in English only (per CLAUDE.md).
3. Estimate the token cost before spawning. If the estimated cost would
   push the 5h window above the threshold for the current status (per the
   feasibility table above), STOP and report to the user.
4. After workers return, do NOT re-summarize their full output back into
   your context. Read only the compressed summary the framework returns.

## Wiki Maintenance Loop

Every regulation/setting change the orchestrator makes triggers, in the
same turn:

1. Update the relevant page(s) in `wiki/architecture/` or `wiki/entities/`.
2. Append a `## [YYYY-MM-DD] action | subject` block to `wiki/log.md`
   summarising what changed and why. (log.md may stay Korean — it is
   factual record, not LLM instruction.)
3. Bump `updated:` on every modified page to today.
4. Mention the change in the user-facing reply.

Failure to do all four = protocol violation.

## Multi-Project Director Slots

When the orchestrator concurrently fills multiple Director slots (e.g.
Mythrill Director + C-Chasm Director), it MUST keep their working
contexts separate in chat (different sessions or explicit "switching to X"
markers). Cross-pollution between project decisions is a protocol
violation; if a decision is genuinely cross-project, escalate to the user
to acknowledge the shared scope before committing it.

## Adding a New Orchestrator Profile

When a new orchestrator-tier model is introduced (e.g. swapping Director
from Opus 4.7 to GPT-5.5):

1. Create `profiles/<name>/config.yaml` with provider/model/system_prompt.
2. Reference this page from the new profile's SOUL.md or system_prompt.
3. Add a row to the Director / Sub-Director / Engine Architect column in
   [[roles]].
4. Smoke-test against the same `{"ok":true,"role":"director"}` JSON probe
   used for tech-artist verification.
5. Log the addition in `wiki/log.md`.

## Related

- [[roles]] — slot definitions
- [[cost-tiers]] — capability-based candidate roster
- [[validators]] — on-demand validation pattern
- [[hermes-core-patches]] — local Hermes mods (env_loader, claude-auth-bypass)

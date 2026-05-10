# Token Budget Reporting

Use this procedure whenever an orchestrator-tier role finishes a task unit and must tell the user what can safely run next.

## Scope

`bash ~/.hermes/bin/quota.sh` is now the single source of truth for the active Hermes account quota. It is model-aware:

- Reads `model.provider`, `model.default`, and optional `model.base_url` from `~/.hermes/config.yaml`.
- Can be overridden with `HERMES_QUOTA_PROVIDER`, `HERMES_QUOTA_MODEL`, and `HERMES_QUOTA_BASE_URL` for explicit probes.
- For `openai-codex/gpt-5.5`, queries the ChatGPT Codex account limits endpoint and selects the model-specific quota bucket when present.
- For Anthropic, falls back to Anthropic OAuth/API account limit probing.

Do not hardcode “Claude Max 5h/7d” in the user-facing closeout unless the active provider is actually Anthropic. The default Hermes path is currently `openai-codex/gpt-5.5`, so the closeout usually reports Codex session/weekly quota.

## Helper

```bash
bash ~/.hermes/bin/quota.sh
```

Operational rule:

- Run it with a 120s tool timeout at task closeout.
- If it times out, rerun with a longer timeout instead of omitting the quota block.
- Do not estimate. If the helper truly fails after retry, say `quota probe failed` and continue without invented numbers.
- Quote the helper output verbatim or nearly verbatim; it already converts reset timestamps to KST and computes time-until-reset.

## User-facing closeout block

Append a compact block like this at the end of the reply:

```text
═══════════════════════════════════════
토큰 잔여 + 다음 작업 가능성
═══════════════════════════════════════
<verbatim output of: bash ~/.hermes/bin/quota.sh>
다음 작업 가능성: GREEN/YELLOW/RED-soft/RED — one-line reason.
```

If the script output already contains `Status:` and `Reason:`, do not recompute those numbers. You may add a Korean one-line interpretation for the next concrete task.

## Feasibility rules

Use the primary/session utilization reported by `quota.sh`:

| Primary/session utilization | Label | Allowed work |
|---|---|---|
| < 50% | GREEN | Heavy worker fan-out OK |
| 50–75% | YELLOW | Light workers only: read-only audits, single-file edits |
| 75–90% | RED-soft | Main 1:1 only; no worker spawn |
| > 90% | RED | Reads/reports only; defer new tasks until reset |

Hard blockers:

- Weekly utilization > 80% → heavy work deferred regardless of session utilization.
- Primary/session reset < 30 minutes away AND primary/session utilization > 60% → do not start heavy work; it may hit the throttle wall before completion.

## Worker cost reference

Use only as a rough planning aid. Never substitute this for a real quota probe.

| Work type | Main input estimate | Worker aggregate input estimate | Typical quota impact |
|---|---:|---:|---:|
| Simple 1:1 reply | ~30K | 0 | <1%pt |
| Single worker, <=5 files | ~5K | ~50K | ~3%pt |
| 3-worker wiki read-only audit | ~10K | ~300K | ~10%pt |
| Large C-Chasm rewrite + patches | ~10K | ~900K | ~30%pt |
| Graphify full semantic re-extraction, wiki ~100 files | ~10K | ~1.5M | ~50%pt |

## Provider-specific notes

- OpenAI Codex OAuth and Anthropic Max OAuth are separate quota pools. Report the active Hermes provider/model, not a stale historical provider.
- Hermes profiles do not automatically separate quota if they share the same underlying account credential.
- Google/Gemini quota is GCP-project scoped; separate keys in the same project do not create separate quota pools.
- Direct pay-per-token API paths must never be selected automatically. If the subscription/OAuth path fails, stop and present options to the user.

## Anti-patterns

- “Probably about 50% remaining” — forbidden. Probe or say the probe failed.
- Reporting Claude Max numbers when Hermes default is `openai-codex/gpt-5.5` — stale rule, forbidden.
- Omitting quota because the first probe exceeded a short tool timeout — rerun with 120s+.
- Manually converting unix reset timestamps in the final reply when the helper already emitted KST — quote the helper output.

## Change history

- 2026-05-08: Updated from Anthropic-only Claude Max reporting to active-provider/model reporting. `quota.sh` now reads Hermes config and reports Codex GPT-5.5 session/weekly limits when that is the active provider.
- 2026-05-06: Introduced at the user’s request with exact quota reporting and GREEN/YELLOW/RED feasibility judgement.

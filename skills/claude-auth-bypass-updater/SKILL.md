---
name: claude-auth-bypass-updater
description: "Auto-check and update hermes-claude-auth bypass when Anthropic changes validation. Runs daily via cron."
version: 1.0.0
author: Hermes Agent
category: mlops
---

# Claude Auth Bypass Auto-Updater

Checks the `kristianvast/hermes-claude-auth` repo for updates and auto-applies them to keep Hermes working with Claude Max/Pro subscription OAuth.

## When to use

- Daily cron job (recommended)
- After `hermes update` — Hermes code changes can break the bypass
- When Claude Opus/Sonnet starts returning 400/429 again

## Check for updates

```bash
# Quick check — compare local vs remote commit hash
LOCAL=$(cd ~/.hermes/hermes-agent/hermes-claude-auth 2>/dev/null && git rev-parse HEAD 2>/dev/null || echo "none")
REMOTE=$(git ls-remote https://github.com/kristianvast/hermes-claude-auth.git HEAD | cut -f1)
if [ "$LOCAL" != "$REMOTE" ]; then
    echo "Update available: $LOCAL → $REMOTE"
else
    echo "Up to date"
fi
```

## Apply update

```bash
curl -fsSL https://raw.githubusercontent.com/kristianvast/hermes-claude-auth/main/install-remote.sh | bash
```

## Verify

```bash
hermes chat -q "say ok" -m claude-opus-4-7 --provider anthropic -Q 2>&1 | grep -q "ok" && echo "✓ Working" || echo "✗ Failed"
```

For the `env_loader` profile-inheritance patch (separate from the Anthropic
bypass but lives in the same "core patches that survive `hermes update`"
class), verify with:

```bash
# Pick any profile that does NOT have its own .env file
hermes chat --profile tech-artist -q 'Output ONLY: {"ok":true}' \
  --ignore-rules --max-turns 1 -t '' 2>&1 | grep -A1 '"ok":true'
```

If either fails, check `hermes auth list` first — the registered provider
id must match `model.provider:` in the profile's `config.yaml`. Google
models register under `gemini` (not `google`); a mismatch produces an
identical "no API key configured" error and is easy to confuse with the
profile-env bug.

### Standard profile smoke-test invocation

For pinging any profile's slot and confirming the model+provider+credentials
chain works end-to-end, use this minimal form (validated 2026-05-07
across orchestrator/researcher/tech-artist/dev-gemma):

```bash
hermes chat --profile <name> \
  -q 'Reply: <SLOT>-OK' \
  --ignore-rules -t '' --max-turns 1 -Q
```

Why each flag:
- `--ignore-rules` skips AGENTS.md / SOUL.md / memory / preloaded-skills
  injection. Brings the request payload down to the bare minimum so the
  test reflects the wire path, not the user's context bloat.
- `-t ''` disables all toolsets — no tool descriptions get attached.
- `--max-turns 1` blocks any agentic loop, single shot.
- `-Q` (quiet) — suppress banner/spinner; the last line of stdout is the
  model's reply.

A passing slot returns the literal `<SLOT>-OK` string. A failing slot
returns an HTTP error code and message that tells you which layer broke
(429 long-context → Anthropic Max OAuth tier; 429 RESOURCE_EXHAUSTED →
Gemini quota; auth → bypass / `.env` chain; "no API key" → provider id
mismatch in `config.yaml`).

## Cron setup

```bash
hermes cron create "every 24h" \
  --name "claude-auth-bypass-check" \
  --prompt "Check kristianvast/hermes-claude-auth for updates. If new commits exist, run the install script. Then verify Claude Opus 4.7 works via hermes chat. Report status."
```

## Pitfalls

- If Anthropic breaks the bypass and the repo hasn't updated yet, the check will pass but Claude won't work
- `hermes update` can change `anthropic_adapter.py` and break the bypass — check after updates
- The bypass uses Python import hooks; if Hermes changes its venv, the hook may need reinstallation
- **Sonnet 1M-context tier 429** — even with bypass active, Hermes defaults Sonnet 4.6 to 1M context (`agent/model_metadata.py`), which Max plan rejects with `"Extra usage is required for long context requests"`. Opus works because the bypass handles it via Claude Code identity, but Sonnet still hits the long-context tier. See `references/sonnet-long-context-429.md`.
- **Profile mode `.env` inheritance** — when Hermes runs with `--profile <name>`, `HERMES_HOME` is set to `~/.hermes/profiles/<name>/`, and `env_loader.py` only loads `<profile>/.env`. Shared API keys in `~/.hermes/.env` are NOT inherited unless the loader is patched. See `references/profile-env-inheritance.md`. After `hermes update` this patch may be reverted — re-apply.
- **Gemini quota is per-GCP-project, not per-API-key** — splitting `GOOGLE_API_KEY` across two profile `.env` files does NOT separate quota if both keys came from the same GCP project. Free-tier RPM/RPD/input-token-per-minute limits are enforced on `project_id`. Fix: mint the second key from a *new* GCP project. See `references/gemini-quota-per-gcp-project.md`.
- **Gemini `*-pro-preview` thinking endpoints are availability-volatile** — same key, same SDK, same prompt can pass 50/50 one week and time out 0/5 the next, with `gemini-3-flash-preview` still responding in 2 s. This is a Google-side capacity / preview-instability signal, NOT a key/SDK/quota fault. Do not add timeout overrides or drop Gemini silently. Run the probe in `references/gemini-preview-model-instability.md` and surface options to the user.

## Provider path discipline (critical)

When `hermes chat` via Max OAuth fails (429, long-context, auth, etc.), DO NOT auto-switch to direct API calls (httpx/curl/SDK against Anthropic). That routes to pay-per-token billing and silently costs the user money. Default behavior: stop, report, ask the user which path to take. This applies to `delegate_task` workers, background terminals, and any subprocess.

## Patch survival across `hermes update`

`hermes-agent/` is in `.gitignore` for the user's `~/.hermes` Git repo, so
core-file patches (e.g. `agent/model_metadata.py`,
`hermes_cli/env_loader.py`, the bypass) cannot be tracked by the user's
config repo. They WILL be reverted by `hermes update`.

Tracking pattern (the user adopted this in `wiki/entities/hermes-core-patches.md`):

- One wiki entity page per "category of patches" — e.g.
  `hermes-core-patches.md` lists every active patch with its file path,
  full patch body inline, rationale, verification command, and date.
- After each `hermes update`, walk the inventory page top-to-bottom,
  re-apply each patch, run its verification command, bump the page's
  `updated:` field.
- Skill `claude-auth-bypass-updater`'s daily cron handles the bypass piece;
  the rest of the inventory needs a manual or scripted pass after upgrades.

Treat the wiki inventory page as the canonical patch ledger. Do NOT rely on
`git diff` against upstream alone, because diffs against a moving upstream
are noisy.

## References

- `references/sonnet-long-context-429.md` — Sonnet 4.6 long-context rejection; root cause + workarounds
- `references/profile-env-inheritance.md` — Hermes profile mode `.env` loading bug and the parent-fallback patch
- `references/gemini-quota-per-gcp-project.md` — Why splitting Gemini keys across profile `.env`s does NOT split quota; the GCP-project fix and a back-to-back diagnostic recipe
- `references/gemini-preview-model-instability.md` — `gemini-*-pro-preview` thinking endpoints can pass 50/50 one week and time out 0/5 the next, even with the same key/SDK. Diagnostic probe + decision tree + forbidden self-corrections (don't add timeouts, don't drop Gemini, don't substitute models without user consent).

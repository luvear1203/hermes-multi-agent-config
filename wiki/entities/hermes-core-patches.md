---
title: "Hermes Core Patches (local modifications to ~/.hermes/hermes-agent)"
created: 2026-05-06
updated: 2026-05-08
type: entity
tags:
  - hermes
  - core-patch
  - infra
sources:
  - "~/.hermes/hermes-agent/hermes_cli/env_loader.py"
  - "~/.hermes/hermes-agent/agent/account_usage.py"
  - "~/.hermes/bin/quota.sh"
  - "[[claude-auth-bypass]]"
confidence: high
---

# Hermes Core Patches

Local modifications to `~/.hermes/hermes-agent/` source. **All patches are lost when `hermes update` runs.** This page is the inventory used to re-apply them after upgrades.

## Active Patches (as of 2026-05-08)

### 1. Profile inheritance for ~/.hermes/.env (env_loader)

**File**: `~/.hermes/hermes-agent/hermes_cli/env_loader.py`
**Function**: `load_hermes_dotenv()`
**Why**: When `hermes chat --profile <name>` is used, `_apply_profile_override()` rewrites `HERMES_HOME` to `~/.hermes/profiles/<name>`. Without the patch, `load_hermes_dotenv()` only searches the profile directory for `.env` and skips `~/.hermes/.env`, so shared API keys (`GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, etc.) become invisible to provider initialization. Result: `HTTP 400 INVALID_ARGUMENT — API key not valid` for every profile call that depends on a parent-level key.

**Patch behaviour**: After loading the profile-local `.env` (if any), the function additionally loads the parent `~/.hermes/.env` as a fallback so missing keys are filled. Profile-local values keep precedence; parent values fill the gaps.

**Patch location** (added inside `load_hermes_dotenv()`):

```python
parent_user_env = None
default_hermes_home = Path.home() / ".hermes"
if home_path.resolve() != default_hermes_home.resolve():
    candidate = default_hermes_home / ".env"
    if candidate.exists():
        parent_user_env = candidate

# ... sanitize parent_user_env if present ...

# After user_env load, before project_env_path load:
if parent_user_env is not None:
    _load_dotenv_with_fallback(parent_user_env, override=not loaded)
    loaded.append(parent_user_env)
```

**Verified**: 2026-05-06 — `hermes chat --profile tech-artist` returns `{"ok":true,...}` from `gemma-4-31b-it`.

### 2. Anthropic billing bypass

See [[claude-auth-bypass]]. Installed via `kristianvast/hermes-claude-auth` import hook + `~/.hermes/patches/anthropic_billing_bypass.py`. Daily cron `claude-auth-bypass-check` keeps it current.

### 3. Active-provider quota reporting

**Files**:
- `~/.hermes/hermes-agent/agent/account_usage.py`
- `~/.hermes/hermes-agent/cli.py`
- `~/.hermes/hermes-agent/gateway/run.py`
- `~/.hermes/bin/quota.sh`

**Why**: End-of-task reporting previously assumed Claude Max 5h/7d quota even after the default Hermes shell moved to `openai-codex/gpt-5.5`. That made closeout reports stale and hid the actual Codex session/weekly quota.

**Patch behaviour**:
- `fetch_account_usage()` accepts an optional `model` and passes it to the Codex usage parser.
- Codex usage parsing selects a model-specific `additional_rate_limits[]` bucket when the active model matches (for example GPT-5.5); otherwise it falls back to the base `rate_limit` bucket.
- CLI and gateway closeout usage calls pass the active agent model into `fetch_account_usage()`.
- `~/.hermes/bin/quota.sh` reads active `model.provider`, `model.default`, and optional `model.base_url` from `~/.hermes/config.yaml`, probes the matching provider/model, prints KST reset times, and emits the GREEN/YELLOW/RED feasibility status.

**Verified**: 2026-05-08 — `pytest tests/test_account_usage.py -q` passed 6/6; `py_compile` passed for `agent/account_usage.py` and `tests/test_account_usage.py`; `bash ~/.hermes/bin/quota.sh` returned `openai-codex / gpt-5.5` with Codex session/weekly quota.

## Re-apply Procedure (after `hermes update`)

1. `git diff` upstream against `~/.hermes/hermes-agent/` to detect lost patches.
2. Re-apply each entry in this page.
3. Run smoke tests:
   - `hermes chat --profile tech-artist -q 'echo {"ok":true}' --ignore-rules --max-turns 1 -t ''` (env_loader patch)
   - `hermes chat -q "say ok" -m claude-opus-4-7 --provider anthropic -Q` (claude-auth-bypass)
   - `cd ~/.hermes/hermes-agent && ./venv/bin/python -m pytest tests/test_account_usage.py -q && bash ~/.hermes/bin/quota.sh` (active-provider quota reporting)
4. Update this page's `updated` date.

## Related

- [[claude-auth-bypass]]
- [[hermes-max-integration]]
- [[multi-agent-system]]

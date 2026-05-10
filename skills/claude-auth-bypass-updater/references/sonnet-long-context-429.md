# Sonnet 4.6 long-context 429 on Hermes via Max OAuth

## Symptom

```
HTTP 429: Extra usage is required for long context requests.
{'type': 'error', 'error': {'type': 'rate_limit_error',
  'message': 'Extra usage is required for long context requests.'}}
```

Triggered even with `kristianvast/hermes-claude-auth` bypass active and
`org_level_disabled / overage_status: rejected`. Opus 4.7 works; Sonnet 4.6
fails. Persists across `--ignore-user-config --ignore-rules -t ''` and even
small (~6K-token) prompts.

## Root cause

Hermes' `agent/model_metadata.py` (~line 145) defaults Sonnet 4.6 to 1M
context length:

```python
DEFAULT_CONTEXT_LENGTHS = {
    ...
    "claude-sonnet-4-6": 1000000,
    "claude-sonnet-4.6": 1000000,
    ...
}
```

The Anthropic adapter then sets the `context-1m-2025-08-07` beta header
(`agent/anthropic_adapter.py`, search `_CONTEXT_1M_BETA`). On Claude Max plan
the 1M tier is paid-only — the server rejects with the long-context 429
regardless of actual prompt size.

Opus is unaffected because the bypass routes Opus traffic through Claude Code
identity which has access to a different limit pool.

## Detection

```bash
# Trigger and grep for the specific message
hermes chat -q 'say ok' -m claude-sonnet-4-6 --provider anthropic --max-turns 1 -t '' 2>&1 \
  | grep -q "Extra usage is required for long context" && echo "1M tier rejection"
```

`drop_context_1m_beta` already exists as a parameter in
`agent/anthropic_adapter.py` (~line 470), but it isn't wired to a public
config knob.

## Workarounds (preference order)

1. **Patch `model_metadata.py`** — change `claude-sonnet-4-6` and
   `claude-sonnet-4.6` entries from `1000000` to `200000`. Survives until
   `hermes update`. Cleanest if you're staying on Sonnet long-term.
2. **Switch to a non-Anthropic Sonnet-tier model** — Gemma 4 31B IT via Google
   AI Studio (free tier), or DeepSeek V4-Pro. Avoids the 1M-tier issue
   entirely. See the studio role table (`wiki/architecture/cost-tiers.md`).
3. **monkeypatch in `sitecustomize.py`** — same pattern the bypass uses;
   override `_CONTEXT_1M_BETA` for Sonnet specifically, leave Opus untouched.

## What NOT to do

- Do NOT auto-switch to direct Anthropic API (httpx/curl). Pay-per-token
  billing fires and the user pays. Always escalate to the user when the
  Max-OAuth path fails.
- Do NOT just retry — the error is non-retryable, the bypass returns
  `Non-retryable error (HTTP 400)` after 3 attempts.
- Do NOT split the prompt into smaller batches and retry on the same Sonnet.
  The 1M-tier flag is request-level, not size-level. Even a 5K-token prompt
  is rejected.

## Verified workarounds in the wild

- Gemma 4 31B IT via Google AI Studio (`provider: gemini`,
  `model: gemma-4-31b-it`) — verified 2026-05-06, free tier, 256K input /
  32K output, OpenAI-compatible endpoint at
  `https://generativelanguage.googleapis.com/v1beta`.

# Gemini / Google AI Studio quota is per-GCP-project, not per-API-key

## TL;DR

If two Hermes profiles both call `gemma-4-31b-it` (or any Gemini model) and
keep hitting `HTTP 429 RESOURCE_EXHAUSTED` even with separate API keys,
the keys are almost certainly issued from the **same GCP project**.

Free-tier quota — `generativelanguage.googleapis.com/generate_content_paid_tier_input_token_count`,
RPM, RPD, etc. — is enforced **per GCP project_id**. All keys minted in the
same project share a single bucket. Splitting `.env` files per profile makes
zero difference if both keys came from the same project.

## How the bug presents

Symptom: two profiles share `GEMINI_API_KEY` (or both `GOOGLE_API_KEY`).
Calling them back-to-back, the second call returns:

```
HTTP 429: Gemini HTTP 429 (RESOURCE_EXHAUSTED): You exceeded your current quota...
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_paid_tier_input_token_count, limit: 16000, model: gemma-4-31b
Please retry in <NN>s.
```

Workaround a user often tries first: put a different key in each profile's
`.env`. **This does not fix it** if both keys are from the same GCP project.
Verifying that the keys are textually different (e.g. md5 of the value)
proves nothing about quota separation.

## The real fix

Create a second GCP project, mint a key from it, put that key in the
profile that should have its own quota:

1. https://aistudio.google.com → top-left project dropdown → "Create project"
2. In the new project, "Get API key"
3. Drop into `~/.hermes/profiles/<other-profile>/.env`:

   ```
   GOOGLE_API_KEY=AIza...new-project-key
   ```

4. `chmod 600` the file
5. Verify quota separation by calling both profiles back-to-back with no
   sleep — both should return successfully. If the second still 429s, the
   keys still share a project.

## Reproduction recipe

```bash
# pre-check the keys differ textually (necessary but NOT sufficient)
for f in ~/.hermes/profiles/<a>/.env ~/.hermes/profiles/<b>/.env; do
  grep -E '^GOOGLE_API_KEY|^GEMINI_API_KEY' "$f" \
    | sed -E 's/.*= *//' | tr -d ' \n' | md5 | tail -c 9
done
# if md5 tails match → same key, copy mistake
# if they differ → keys are different, but they may STILL share a GCP project

# real test: back-to-back call, no sleep
hermes chat --profile <a> -q 'A-OK' --ignore-rules -t '' --max-turns 1 -Q
hermes chat --profile <b> -q 'B-OK' --ignore-rules -t '' --max-turns 1 -Q
# if (b) returns 429 → keys are in the same project, follow "real fix" above
```

## Why hermes profile `.env` IS doing its job

Sometimes 429 also happens because `hermes_cli/env_loader.py` is reverted
after `hermes update` and profile `.env` no longer overrides the parent.
Distinguish the two failure modes:

- **env_loader regressed** → both profiles end up reading the same key from
  parent `~/.hermes/.env` regardless of what's in the profile-local file.
  Fix: re-apply the env_loader patch (`references/profile-env-inheritance.md`).
- **GCP project shared** → profile `.env` is loaded correctly, the keys
  ARE different, but quota is per-project. Fix: new GCP project.

A quick way to tell them apart: read
`hermes-agent/hermes_cli/env_loader.py` and confirm the profile-local
`.env` is loaded with `override=True` while the parent is loaded with
`override=not loaded` (i.e. fallback only). If that code path is intact,
the bug is the GCP-project one.

## Per-slot key inventory

The user keeps `tech-artist` and `dev-gemma` on separate GCP projects.
They share the same model (`gemma-4-31b-it`) but quota is fully separated.
Concurrent `delegate_task` to both is safe; the per-slot 16K input/min
limit still applies inside each project, so don't fan a single slot out
in parallel.

If a third Gemma slot is ever needed, mint a third GCP project. Don't
share keys between roles.

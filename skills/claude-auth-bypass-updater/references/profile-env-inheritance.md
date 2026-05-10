# Hermes profile mode `.env` inheritance

## Symptom

Running `hermes chat --profile <name>` fails to find API keys that are present
in `~/.hermes/.env`. Logs show:

```
resolve_provider_client: provider <name> has no API key configured
  (tried: GOOGLE_API_KEY, GEMINI_API_KEY)
```

Yet the same key works fine without `--profile`, and a manual
`source ~/.hermes/.env && hermes chat ...` also works.

## Root cause

`hermes_cli/main.py:_apply_profile_override` runs at startup and sets
`os.environ["HERMES_HOME"] = ~/.hermes/profiles/<name>`. Then
`hermes_cli/env_loader.py:load_hermes_dotenv()` only loads
`<HERMES_HOME>/.env` (= the profile dir's own `.env`, which usually doesn't
exist). It never falls back to the parent `~/.hermes/.env`. Result: shared
API keys never reach the provider lookup.

## Patch (verified 2026-05-06, Hermes v0.12.0)

`hermes_cli/env_loader.py`, function `load_hermes_dotenv`:

```python
def load_hermes_dotenv(*, hermes_home=None, project_env=None):
    loaded = []
    home_path = Path(hermes_home or os.getenv("HERMES_HOME", Path.home() / ".hermes"))
    user_env = home_path / ".env"
    project_env_path = Path(project_env) if project_env else None

    # Profile inheritance: if HERMES_HOME points to a profile dir, also
    # load the parent ~/.hermes/.env so shared keys propagate.
    parent_user_env = None
    default_hermes_home = Path.home() / ".hermes"
    if home_path.resolve() != default_hermes_home.resolve():
        candidate = default_hermes_home / ".env"
        if candidate.exists():
            parent_user_env = candidate

    if user_env.exists():
        _sanitize_env_file_if_needed(user_env)
    if parent_user_env is not None:
        _sanitize_env_file_if_needed(parent_user_env)
    if project_env_path and project_env_path.exists():
        _sanitize_env_file_if_needed(project_env_path)

    if user_env.exists():
        _load_dotenv_with_fallback(user_env, override=True)
        loaded.append(user_env)

    if parent_user_env is not None:
        _load_dotenv_with_fallback(parent_user_env, override=not loaded)
        loaded.append(parent_user_env)

    if project_env_path and project_env_path.exists():
        _load_dotenv_with_fallback(project_env_path, override=not loaded)
        loaded.append(project_env_path)

    return loaded
```

Profile-local `.env` still wins where set; parent `.env` only fills missing
keys.

## Verification recipe

```bash
# Before patch — should fail with "no API key configured"
hermes chat --profile <profile_with_no_local_env> -q 'say ok' \
  --ignore-rules --max-turns 1 -t '' 2>&1 | grep -i 'api key'

# After patch — should return content
hermes chat --profile <profile_with_no_local_env> -q 'say ok' \
  --ignore-rules --max-turns 1 -t '' 2>&1 | grep -A1 'Output ONLY'
```

## Provider-id pitfall

Adjacent issue worth checking when keys appear missing:
`profiles/<name>/config.yaml` `model.provider:` value must match Hermes'
internal provider id. Google models use `provider: gemini` (not `google`).
Mismatch → `auth.py:200~207` lookup fails, identical "no API key" error.
Confirm via `hermes auth list` — the registered provider name is the right
value to use.

## Why upstream

Worth opening a Hermes Agent issue/PR; profile inheritance for shared API
keys is the obvious user expectation.

# macOS Python Environment — Pitfalls

User machine: Apple Silicon macOS, two Python interpreters coexist.

## Which Python is which

| Path | Source | pip flag support | PEP 668 |
|---|---|---|---|
| `/usr/bin/python3` | Apple Command Line Tools | NO `--break-system-packages` | externally-managed, blocks pip |
| `/opt/homebrew/bin/python3` | Homebrew (currently 3.14) | YES `--break-system-packages` | externally-managed, but flag works |

`which python3` returns BOTH (system first in some shells). Always disambiguate explicitly.

## Correct install command on this machine

```
/opt/homebrew/bin/pip3 install --break-system-packages <pkg>
```

Failure modes seen 2026-05-07:

1. `pip install ...` → `bash: pip: command not found` (no system pip).
2. `python3 -m pip install --break-system-packages pillow` → `no such option: --break-system-packages` (used Apple's Python).
3. Plain `pip3 install pillow` would have hit PEP 668 `error: externally-managed-environment`.

## Better long-term: venv per project

For non-throwaway work, prefer:
```
/opt/homebrew/bin/python3 -m venv .venv
source .venv/bin/activate
pip install <pkg>
```
No `--break-system-packages` needed; isolates from system. Use this when the script will live more than one session.

## HOME path quirk

User GitHub handle = `luvear1203` (in memory/wiki) but actual macOS `$HOME = /Users/main`. Don't assume `~` expands to `/Users/luvear1203` — it expands to `/Users/main`. Use `$HOME` or `os.path.expanduser('~')` rather than hardcoding either path.

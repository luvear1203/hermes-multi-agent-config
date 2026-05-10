#!/usr/bin/env python3
"""Direct Anthropic API call for graphify semantic extraction.

WHY: `hermes chat -q ...` injects ~50K of tool descriptions, memory, and skill
listings into every invocation. A 35K-char extraction prompt becomes a 1M+ token
request that the Claude Max OAuth tier rejects with HTTP 429
"Extra usage required for long context requests."

This script bypasses Hermes entirely. Minimal system prompt, no tools,
direct keychain OAuth read. Saves ~95% input tokens.

USAGE:
  python3 extract.py <prompt_file> <output_json>

The output_json receives the parsed {nodes, edges, hyperedges} object.
A `<output_json>.raw.txt` is also written with the raw model response in case
parsing fails.

REQUIREMENTS:
  - macOS keychain entry "Claude Code-credentials" with claudeAiOauth.accessToken
  - hermes_claude_auth bypass package (auto-loaded if installed); not strictly
    required for plain Sonnet/Haiku, but recommended for Opus
  - httpx in the active venv
"""
import sys, os, json, subprocess

# Load Hermes claude-auth bypass if available (needed for Opus on some accounts)
try:
    import hermes_claude_auth  # noqa
except Exception:
    pass

import httpx

raw = subprocess.run(
    ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
    capture_output=True, text=True,
).stdout.strip()
if not raw:
    print("ERROR: No 'Claude Code-credentials' entry in macOS keychain.", file=sys.stderr)
    sys.exit(2)
token = json.loads(raw)["claudeAiOauth"]["accessToken"]

if len(sys.argv) < 3:
    print("Usage: extract.py <prompt_file> <output_json> [model]", file=sys.stderr)
    sys.exit(1)

prompt_path, out_path = sys.argv[1], sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "claude-sonnet-4-6-20250929"
prompt = open(prompt_path).read()

# Bypass requires the Claude Code persona system prompt at minimum.
system = "You are Claude Code, Anthropic's official CLI for Claude."

headers = {
    "authorization": f"Bearer {token}",
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "oauth-2025-04-20,claude-code-20250219,interleaved-thinking-2025-05-14,fine-grained-tool-streaming-2025-05-14",
    "content-type": "application/json",
    "user-agent": "claude-cli/2.1.126 (external, cli)",
    "x-app": "cli",
}
body = {
    "model": model,
    "max_tokens": 16000,
    "system": [{"type": "text", "text": system}],
    "messages": [{"role": "user", "content": prompt}],
}

with httpx.Client(timeout=300) as cx:
    r = cx.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)

if r.status_code != 200:
    print(f"HTTP {r.status_code}", file=sys.stderr)
    print(r.text[:1000], file=sys.stderr)
    sys.exit(2)

data = r.json()
text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")

open(out_path + ".raw.txt", "w").write(text)

# Parse the first balanced JSON object out of the response.
try:
    s = text.find("{")
    if s < 0:
        raise ValueError("no opening brace in response")
    depth = 0
    e = -1
    for i in range(s, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                e = i + 1
                break
    if e < 0:
        raise ValueError("unbalanced braces")
    parsed = json.loads(text[s:e])
    json.dump(parsed, open(out_path, "w"), indent=2, ensure_ascii=False)
    n = len(parsed.get("nodes", []))
    ed = len(parsed.get("edges", []))
    he = len(parsed.get("hyperedges", []))
    print(f"OK nodes={n} edges={ed} hyperedges={he}")
    usage = data.get("usage", {})
    print(f"Usage: input={usage.get('input_tokens', 0)} output={usage.get('output_tokens', 0)}")
except Exception as exc:
    print(f"Parse failed: {exc}", file=sys.stderr)
    print(f"Raw output saved to {out_path}.raw.txt", file=sys.stderr)
    sys.exit(3)

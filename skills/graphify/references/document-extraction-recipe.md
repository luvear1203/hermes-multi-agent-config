# Document/Markdown Semantic Extraction Recipe

When `/graphify <path> --update` reports document changes (not code-only) and the AI must run semantic extraction on the changed files, the worker dispatch is non-obvious because of three independent failure modes. This file documents the working invocation pattern derived from a session where all three failures hit in sequence.

## Failure modes that you WILL hit if you skip the smoke test

| Symptom | Root cause | Fix |
|---|---|---|
| HTTP 429 "Extra usage is required for long context requests." | `hermes chat` defaults inject ~50K tokens of system prompt, tools, AGENTS.md, memory, skills index. Combined with the file payload this exceeds Sonnet OAuth standard-tier 200K. | Use `--ignore-user-config --ignore-rules -t '' --max-turns 1` to strip injection. |
| HTTP 401 "Invalid authentication credentials." | `hermes_claude_auth` bypass is a Python import hook tied to a specific venv. Calling Anthropic API directly with `httpx` from a different venv (or no venv) reads the token but Anthropic rejects it because the request fingerprint doesn't match Claude Code. | Use `hermes chat` (which auto-loads the bypass) instead of bare `curl`/`httpx`. |
| Parser returns garbage with `{"id": "filestem_entityname", "label": "Human Readable Name", ...}` | The prompt's literal JSON SCHEMA example was at the top of the file. Naive `find('{')` matched it. | Wrap real output in sentinels OR scan for the LAST balanced `{...}`. |

## Mandatory pre-flight: smoke test ONE batch first

Before fanning out to N parallel workers, run exactly one batch end-to-end and confirm JSON parses. Cost of skipping: 3 wasted launches, user frustration, kills.

```bash
# 1. Build prompt for batch1 only
cat > /tmp/gx_smoke.prompt.md <<'EOF'
You are a knowledge graph extractor. Output ONE JSON object between sentinels:
<<<JSON>>>
{ "nodes": [...], "edges": [...], "hyperedges": [...] }
<<</JSON>>>

(schema details, files, etc.)
EOF

# 2. Smoke test (foreground, ~30s for ~5 small markdown files)
hermes chat -q "$(cat /tmp/gx_smoke.prompt.md)" \
  -m claude-sonnet-4-6 --provider anthropic \
  --ignore-user-config --ignore-rules \
  -t '' --max-turns 1 \
  > /tmp/gx_smoke.out 2> /tmp/gx_smoke.err

# 3. Parse and verify
python3 -c "
import re, json
txt = open('/tmp/gx_smoke.out').read()
m = re.search(r'<<<JSON>>>(.*?)<<</JSON>>>', txt, re.DOTALL)
if not m: raise SystemExit('NO SENTINEL FOUND - reprompt')
d = json.loads(m.group(1).strip())
print(f'OK nodes={len(d[\"nodes\"])} edges={len(d[\"edges\"])}')
"
```

If smoke test passes, fan out. If it fails, iterate on prompt/flags until it passes.

## Working batch dispatch (only after smoke test passes)

Split changed-files list into batches of 5-10 markdown files (NOT 30 — long context drains 5h window faster, and large batches lose precision). For each batch:

```bash
hermes chat -q "$(cat /tmp/gx_batchN.prompt.md)" \
  -m claude-sonnet-4-6 --provider anthropic \
  --ignore-user-config --ignore-rules \
  -t '' --max-turns 1 \
  > /tmp/gx_batchN.out 2> /tmp/gx_batchN.err
```

Run sequentially or in `terminal(background=true, notify_on_complete=true)` for parallelism. Keep concurrency ≤3 unless you've measured rate-limit headroom.

## Prompt design that survives the gauntlet

1. Wrap expected output between unique sentinels: `<<<JSON>>>` and `<<</JSON>>>`. Without this the parser will catch the schema example.
2. Embed each input file inline between `========== FILE: <path> ==========` and `========== END FILE ==========`.
3. End with a single explicit instruction: "Output ONLY the JSON between the sentinels. No prose. No markdown fences."
4. Keep the schema explanation under 1500 tokens — Sonnet doesn't need 5000 tokens of rules to handle wikilink extraction.

## Merge / build / cluster / labels / HTML

Once all batches return parsed JSON dicts:

1. Concatenate all `nodes`, `edges`, `hyperedges` arrays.
2. Dedupe nodes by `id` (first occurrence wins).
3. Drop dangling edges (source or target not in node set) — log count for the audit.
4. Load existing `graphify-out/graph.json`, merge with new extraction (NetworkX `G.update()`).
5. Re-run `graphify.cluster.cluster(G)` and `score_all`.
6. Generate community labels yourself (not "Community 0/1/2"). Read top-5 nodes per community, write 2-5 word names.
7. `graphify.export.to_html(G, communities, ..., community_labels=labels)` and `to_json(...)` to write outputs.
8. Update `manifest.json` via `graphify.detect.save_manifest(detect['files'])`.

See parent SKILL.md Steps 4–9 for the actual Python commands.

## When to fall back to other models

If Sonnet OAuth still 429s after `--ignore-*` flags (e.g. user is heavily through their 5h window), fall back order:

1. **Haiku 4.5** (Max OAuth) — same `hermes chat` flags, much cheaper context. Quality drop on inferred edges but acceptable for re-extraction.
2. **DeepSeek V4-Pro** (`-m deepseek-v4-pro --provider deepseek`) — 5h-window-free, costs USD. User is cost-sensitive — confirm before using.
3. **Sequential single-file extraction** with the OpenClaw/single-agent path from parent SKILL.md.

## What NOT to do (anti-patterns from real session)

- ❌ Launch 3 parallel `hermes chat` workers without confirming any of them work. → 3 simultaneous 429s.
- ❌ Switch to direct `httpx.post` thinking it's "lighter" without first confirming bypass loads in the new venv. → 3 simultaneous 401s.
- ❌ Re-launch with `--ignore-user-config` immediately after the second failure without smoke-testing one batch. → user kills with "멈춰".
- ❌ Use a parser that grabs the first `{...}` block when the prompt contains a JSON schema example.

## Audit fields to record per run

After successful run, append to `graphify-out/cost.json`:
```json
{
  "date": "ISO8601",
  "input_tokens": <sum-of-batches>,
  "output_tokens": <sum-of-batches>,
  "files": <count>,
  "workers": <batch-count>,
  "model": "claude-sonnet-4-6",
  "transport": "hermes-chat-ignore-config"
}
```

This lets the next session reason about cost before dispatching.

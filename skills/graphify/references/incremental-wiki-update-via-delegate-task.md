# Incremental Wiki Update via delegate_task (in-session path)

When the agent IS the orchestrator (this conversation runs Opus or Sonnet directly with `delegate_task` tool available), graphify wiki updates do NOT need to subprocess `hermes chat`. The cleaner path is to spawn workers via `delegate_task` and merge results in-process. This file documents the working invocation derived from sessions on 2026-05-07 (33-file initial bulk + 2-file incremental).

This is a complement to `references/document-extraction-recipe.md` — which assumes you must subprocess `hermes chat` (e.g. cron, CI, external script). Use the recipe below when you have `delegate_task` in your toolset.

## Decision: delegate_task vs hermes chat subprocess

| Situation | Use |
|---|---|
| You are running interactively as orchestrator with delegate_task tool | **delegate_task** (this file) |
| You are a cron job / CI / external script / hermes chat itself | `hermes chat` subprocess (`document-extraction-recipe.md`) |
| Cost measurement / token attribution per worker | delegate_task (returns `tokens` and `api_calls` in result) |
| Need to keep workers fully isolated from agent context | hermes chat subprocess (no shared state) |

Both paths use the same prompt schema. Only the dispatch mechanism differs.

## Pre-flight

```python
# 1) Detect changed files. Save the result for chunking.
import json
from pathlib import Path
from graphify.detect import detect_incremental
result = detect_incremental(Path('/Users/main/.hermes/wiki'))
print('new_total:', result.get('new_total'))
Path('/Users/main/.hermes/wiki/graphify-out/.graphify_incremental.json').write_text(json.dumps(result))
```

If `new_total == 0`: nothing to do, stop. If `new_total <= 5`: dispatch ONE worker. If 6-30: 2-3 workers. If >30: split into batches of ~11 files each, dispatch ≤3 workers per `delegate_task` call (Anthropic Max OAuth handles 3 concurrent fine).

## Chunking

```python
files = []  # absolute paths from result['new_files'][category]
chunks = [files[i:i+11] for i in range(0, len(files), 11)]
for i, c in enumerate(chunks):
    Path(f'/tmp/graphify_chunk_{i}.json').write_text(json.dumps(c))
```

Don't fan out without first knowing the byte budget per worker. ~11 markdown files of avg 3KB each = ~35KB input. Workers see Read_file output (~5x literal bytes once tokenised), so a chunk that looks small on disk can still hit 200K+ tokens at the worker. The 33-file initial run consumed up to 333K input tokens on the largest chunk (chunk 2 contained log.md @ 17KB and session-2026-05-04.md @ 9KB); plan accordingly.

## Worker dispatch (delegate_task)

```
delegate_task tasks:
  - goal: "Semantic graph extraction on chunk N. Read /tmp/graphify_chunk_N.json (array of paths). Emit JSON to /tmp/graphify_out_N.json. Do not print JSON to chat."
    context: |
      You are running graphify Step 3 Part B (semantic extraction) for chunk N/total.
      File list: read /tmp/graphify_chunk_N.json (a JSON array of absolute paths).

      For each markdown file:
      - Parse YAML frontmatter (title, type, tags, sources) + body.
      - ONE document node: id = filename stem (slug, Hangul allowed), label = H1 or frontmatter title, file_type = frontmatter `type` if in [entity|project|system|character|concept|architecture|comparison|query|summary] else 'document', source_file = path relative to ~/.hermes/wiki/.
      - For every UNIQUE [[wikilink]] target: ONE edge from doc node to target-slug, relation='references', confidence='EXTRACTED', confidence_score=1.0. Dedupe; emit one edge per unique target. If target not in chunk, still emit a node stub (label=link text, file_type='document').
      - Up to 5 INFERRED 'conceptually_related_to' edges per file (0.6-0.85), only when two docs share a clearly named concept not already wikilinked.
      - Max 2 hyperedges per chunk.

      Schema:
        Node: {id, label, file_type, source_file, source_location:null, source_url:null, captured_at:null, author:null, contributor:null}
        Edge: {source, target, relation, confidence, confidence_score, source_file, source_location:null, weight:1.0}
        Hyperedge: {id, label, nodes:[ids], relation, confidence, confidence_score, source_file}

      Final JSON: {"nodes":[...], "edges":[...], "hyperedges":[...], "input_tokens":0, "output_tokens":0}
      Write to /tmp/graphify_out_N.json. Reply ONLY: 'DONE: N nodes, M edges, K hyperedges'.

      Rules: no invented edges. English labels EXCEPT preserve Korean titles in `label`. Slugify ids consistently.
    toolsets: ["file"]
```

Toolset `["file"]` is critical — the worker must have `read_file` and `write_file` and nothing else. Giving it `terminal` invites tool drift; giving it everything blows the system prompt.

For incremental updates with 2 files, dispatch ONE worker (no chunking overhead). For 33-file initial bulk, 3 workers of 11 files each completed in ~3 minutes.

## Merge in-process

```python
import json
from pathlib import Path

# 1) Concatenate worker outputs
all_n, all_e, all_h = [], [], []
for i in range(num_chunks):
    d = json.loads(Path(f'/tmp/graphify_out_{i}.json').read_text())
    all_n += d.get('nodes', [])
    all_e += d.get('edges', [])
    all_h += d.get('hyperedges', [])

# 2) Load existing graph (graph.json uses 'links' key, not 'edges')
g = json.loads(Path('/Users/main/.hermes/wiki/graphify-out/graph.json').read_text())
existing_ids = {n['id'] for n in g['nodes']}
existing_edges = {(l['source'], l['target'], l.get('relation','')) for l in g['links']}

# 3) Dedup-add nodes
for n in all_n:
    if n['id'] not in existing_ids:
        g['nodes'].append(n); existing_ids.add(n['id'])

# 4) Dedup-add edges (using new->old key shape)
for e in all_e:
    key = (e['source'], e['target'], e.get('relation',''))
    if key not in existing_edges:
        g['links'].append({
            'source': e['source'], 'target': e['target'],
            'relation': e['relation'],
            'confidence': e.get('confidence','EXTRACTED'),
            'confidence_score': e.get('confidence_score', 1.0),
            'source_file': e.get('source_file',''),
            'weight': e.get('weight', 1.0),
        })
        existing_edges.add(key)

# 5) Build extraction-shape dict for graphify.build_from_json
extraction = {
    'nodes': g['nodes'],
    'edges': [...],  # rebuild from g['links'] in extract format
    'hyperedges': g.get('hyperedges', []) + all_h,
    'input_tokens': sum_input,
    'output_tokens': sum_output,
}
Path('/tmp/graphify_extract_full.json').write_text(json.dumps(extraction))
```

## Build / cluster / HTML / manifest

```bash
cd ~/.hermes/wiki && /opt/homebrew/bin/python3 <<'EOF'
import json
from pathlib import Path
from graphify.build import build_from_json
from graphify.cluster import cluster, score_all
from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.export import to_json, to_html
from graphify.report import generate
from graphify.detect import detect, save_manifest

extraction = json.loads(Path('/tmp/graphify_extract_full.json').read_text())
G = build_from_json(extraction)
communities = cluster(G)
cohesion = score_all(G, communities)
gods = god_nodes(G)
surprises = surprising_connections(G, communities)
labels = {cid: f'Community {cid}' for cid in communities}  # placeholder labels
questions = suggest_questions(G, communities, labels)

detection = detect(Path('.'))
tokens = {'input': extraction.get('input_tokens',0), 'output': extraction.get('output_tokens',0)}
report = generate(G, communities, cohesion, labels, gods, surprises, detection, tokens, '.', suggested_questions=questions)
Path('graphify-out/GRAPH_REPORT.md').write_text(report)
to_json(G, communities, 'graphify-out/graph.json')
to_html(G, communities, 'graphify-out/graph.html', community_labels=labels)
save_manifest(detection['files'])
EOF
```

`save_manifest` MUST be called with `detection['files']` (current state), not the incremental result. Otherwise the next `detect_incremental` will re-flag everything as new.

## Verify

```bash
cd ~/.hermes/wiki && /opt/homebrew/bin/python3 -c "
import json, os, time
m = json.load(open('graphify-out/manifest.json'))
print(f'Manifest entries: {len(m)}')
# Spot-check: were the just-changed files synced?
for rel in ['log.md', 'architecture/roles.md']:
    full = os.path.join('/Users/main/.hermes/wiki', rel)
    if full in m:
        synced = abs(os.path.getmtime(full) - m[full]['mtime']) < 1
        print(f'  {chr(0x2713) if synced else chr(0x2717)} {rel}')
"
```

## Cleanup

```bash
rm -f /tmp/graphify_chunk_*.json /tmp/graphify_out_*.json /tmp/graphify_files.json /tmp/graphify_extract_*.json
rm -f /Users/main/.hermes/wiki/graphify-out/.graphify_incremental.json
```

graphify-out/ is gitignored — no commit needed. wiki source files (`*.md`) are committed normally; the rebuilt graph follows on disk.

## Cost benchmark (Opus 4.7, 2026-05-07)

| Run | Files | Workers | Input tokens | Output tokens | Wall time |
|---|---|---|---|---|---|
| Initial bulk re-extraction | 33 | 3 (parallel) | 493K | 41K | ~3 min |
| 2-file incremental | 2 | 1 | 44K | 2.6K | 31 sec |

For a single small incremental (≤3 files), one worker beats three workers because of shared overhead. For 30+ files, parallel wins.

## Pitfalls

- **Schema mismatch warning**: `cost-tiers.md` uses `type: architecture` in frontmatter; graphify's allowed file_types are `[code, concept, document, image, paper, rationale]`. The build emits a non-fatal warning but the node still gets `file_type='architecture'`. Either change the frontmatter to `concept` or extend graphify's schema. Doesn't block the run.
- **`save_manifest` argument shape**: takes the `files` dict from `detect()`, NOT a flat list. The dict structure is `{category: [paths]}`.
- **Worker output written to /tmp**: don't write to `~/.hermes/wiki/graphify-out/` directly — `detect()` will pick up worker artifacts as docs and create cycles.
- **Don't dispatch worker without `toolsets: ["file"]`**: full toolset workers can wander into terminal/git operations and cost 5x tokens.
- **delegate_task model defaults to caller's model**: workers will run on the same model as the orchestrator unless overridden. For wiki extraction, Opus is overkill — Sonnet 4.5 is cheaper and equally accurate. Override via `delegate_task` model param if available.

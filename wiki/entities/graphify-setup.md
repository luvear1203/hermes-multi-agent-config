---
title: Graphify Knowledge Graph
created: 2026-05-03
updated: 2026-05-07
type: entity
tags: [open-source, visualization, knowledge-graph]
sources: [https://github.com/safishamsi/graphify]
confidence: high
---

# Graphify Knowledge Graph

Hermes wiki와 Hermes Agent 코드베이스를 보조하는 로컬 지식 그래프 도구.

## Install

```bash
cd ~/.hermes
git clone https://github.com/safishamsi/graphify.git
cd graphify
python3 -m pip install --break-system-packages -e .
```

## Usage

Code AST graph:

```bash
graphify update hermes-agent/     # 코드베이스 분석 (AST only, no API)
graphify query "How does tool calling work?"   # 그래프 기반 질의
graphify explain "AIAgent"        # 특정 노드 설명
graphify path "AIAgent" "handle_function_call"  # 두 노드 간 경로
```

Wiki semantic graph:

```bash
graphify check-update wiki
graphify cluster-only wiki --no-viz
```

## Current Wiki Graph Stats

Source: `wiki/graphify-out/GRAPH_REPORT.md` after
`graphify cluster-only wiki --no-viz` on 2026-05-07.

- Nodes: 246
- Edges: 633
- Communities: 14
- Output: `wiki/graphify-out/`

Last full semantic corpus check before cluster-only regeneration: 109 files,
approximately 100,504 words.

## Current Code Graph Stats

Source: initial Hermes Agent code graph generated on 2026-05-03.

- Nodes: 54,648
- Edges: 100,005
- Communities: 1,920
- Output: `hermes-agent/graphify-out/`

## Note

- `graphify update <path>` is AST-only. On a markdown-only wiki update it can report `No code files found`, so this is not a semantic wiki refresh.
- Wiki semantic extraction should be treated as a separate graphify pass, then clustering/report regeneration can be run from the existing `graph.json`.
- `graphify cluster-only wiki --no-viz` is safe for local report regeneration from the current graph. It does not ingest new markdown semantics by itself.
- `graphify-out/` and `.graphify_*.json` are local generated artifacts and remain Git-ignored.
- Obsidian Graph View remains useful for manual wikilink navigation; Graphify is used for semantic graph inspection and code AST graphing.

## 2026-05-07 Control Plane Reflection

The new [[local-agent-control-plane]] page and the rewritten [[multi-agent-system]]
page establish the dashboard/control-plane direction:

- Hermes and OpenClaw remain terminal-first execution runtimes.
- The local dashboard becomes the readable mission board, profile registry, knowledge console, and approval surface.
- `CodexCliAdapter`, `HermesProfileAdapter`, and `ManualAdapter` are the first adapter boundary candidates.
- Claude Opus and Sonnet calls are currently deferred while subscription token limits are active.
- Full semantic wiki re-extraction is deferred for the same reason; local clustering was regenerated from the existing graph only.

## Related

- [[llm-wiki-setup]]
- [[multi-agent-system]]
- [[local-agent-control-plane]]

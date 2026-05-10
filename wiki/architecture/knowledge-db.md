---
title: Knowledge DB — Qdrant-backed semantic search index
created: 2026-05-10
updated: 2026-05-10
type: architecture
tags: [knowledge-db, qdrant, rag, multi-agent]
sources:
  - "docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md"
  - "https://qdrant.tech/documentation/"
  - "https://docs.voyageai.com/"
confidence: high
---

# Knowledge DB

A Qdrant-backed semantic index over wiki + external knowledge. Primary purpose: reduce token cost when traversing wiki at LLM call time. Secondary: persist external research with forced provenance and dedupe.

## Two-Tier Search (Wiki-First → KB-Second)

See `~/.hermes/patches/wiki_first_kb_second.py`. Wiki page graph traversal first; on miss fall through to `wiki_*` collections, then `kb_*` collections.

## Collections (12)

`wiki_entities` · `wiki_concepts` · `wiki_architecture` · `kb_papers` · `kb_oss_projects` · `kb_industry_solutions` · `kb_lessons_learned` · `kb_dev_docs` · `mythrill_code` · `chat_memory` · `personal_notes` · `topics`.

vector dim 1024, cosine distance, HNSW (m=16, ef_construct=100), int8 scalar quantization. `topics`는 1-dim placeholder (Qdrant은 size=0 거부, 검색은 payload filter).

## Forced Payload (every chunk)

`source_url`, `content_hash` (sha256 dedupe key), `retrieved_at` (ISO8601), `citation` (markdown), `relevance_topics`, `language`, `embedding_model`, `confidence`. Validation enforced in `kb_tools.kb_upsert`.

## Embedding

- Phase 1: Voyage-3 (1024 dim, paid ~$0.10/M tokens). Free tier ~3 RPM, ~10K TPM, 50M tokens/month.
- Phase 2: BGE-M3 (1024 dim, local). Same dim → schema unchanged on swap.

운영 제약 (2026-05-10): Voyage Free TPM 한도로 Hermes 25k 토큰 system prompt가 1요청 한도 초과 가능 → wiki 인덱싱 배치를 5 페이지·25s sleep로 분할.

## Toolsets

- `~/.hermes/skills/knowledge-db/kb_tools.py`: `kb_search`, `kb_upsert`, `kb_upsert_batch`, `kb_topic_register`, `kb_topic_list`, `kb_stats`, `compute_content_hash`, `validate_payload`, `_to_qdrant_id`.
- `~/.hermes/skills/research-external/external_tools.py`: `arxiv_search`, `semantic_scholar_search`, `github_search`, `tavily_search`, `normalize_chunk` + backoff retry.

## Qdrant Point ID 제약

Qdrant는 uint64 또는 UUID만 허용. `_to_qdrant_id(raw)`가 임의 문자열을 deterministic UUID5로 변환 (NAMESPACE_URL). content_hash hex 32-char도 동일 처리.

## graphify 통합 (Phase 1)

`wiki/graphify-out/`의 semantic 추출 결과 (246 nodes / 633 edges)는 향후 cron으로 KB upsert 예정 (Step 4).

## Related

[[continuous-research-loop]] · [[qdrant-instance]] · [[wiki-token-cost-reduction]] · [[orchestrator-protocol]] · [[multi-agent-system]] · [[model-prompting-conventions]]

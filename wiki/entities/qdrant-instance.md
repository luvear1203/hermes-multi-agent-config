---
title: Qdrant Instance — Hermes Knowledge DB cluster
created: 2026-05-10
updated: 2026-05-10
type: entity
tags: [knowledge-db, qdrant, infrastructure]
sources:
  - "docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md"
  - "https://cloud.qdrant.io"
confidence: high
---

# Qdrant Instance

Hermes Knowledge DB의 단일 Qdrant cluster.

## Phase 1 (현재, 2026-05-10~)

- **Provider**: Qdrant Cloud (managed)
- **Region**: GCP `australia-southeast1-0`
- **Tier**: Free (1GB RAM, 4GB storage). 사용량 증가 시 paid ~$25/월
- **Endpoint**: `~/.hermes/.env`의 `QDRANT_URL` (포트 6333)
- **Auth**: `QDRANT_API_KEY` (JWT 형식)
- **Billing surface**: 신규 (사용자 승인 게이트 통과, spec 2026-05-10)

## Phase 2 (예정)

자체 머신(Mac Studio M5 Ultra 또는 DGX Spark) 도착 후 Qdrant 셀프호스트(도커). Snapshot export/import로 마이그레이션 (저장 형식 호환).

## Collections

[[knowledge-db]] §Collections 참조 — 12개, 1024 dim, cosine + HNSW + int8 quantization.

## 관리

- Cluster 생성·키 발급: `https://cloud.qdrant.io`
- 컬렉션 생성 스크립트: `scripts/create_collections.py` (멱등)
- 인덱싱 스크립트: `scripts/index_wiki.py`, `scripts/index_mythrill.py`

## Related

[[knowledge-db]] · [[wiki-token-cost-reduction]]

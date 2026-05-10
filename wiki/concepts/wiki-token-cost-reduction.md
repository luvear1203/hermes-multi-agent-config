---
title: Wiki Token Cost Reduction — KB-backed Wiki-First search rationale
created: 2026-05-10
updated: 2026-05-10
type: concept
tags: [knowledge-db, cost, token, optimization]
sources:
  - "docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md"
confidence: high
---

# Wiki Token Cost Reduction

## 문제

기존 Wiki-First 검색은 LLM에 wiki 전체(또는 큰 부분)를 system prompt에 주입 → 매 호출마다 토큰 비용 누적. 한국어 wiki는 평균 영어 대비 ~2.08× 더 많은 토큰 (cl100k_base 기준, [[CLAUDE]] 참조).

## 해결: Knowledge DB 매개

LLM 호출 시점에 wiki 전체를 주입하지 않고, [[knowledge-db]]의 semantic search로 query 관련 청크만 top-k 추출 → 답변에 인용. 호출당 system prompt 크기를 일정 상한(예: 5K 토큰)으로 고정 가능.

## 비용 모델 (2026-05-10 spec §11)

| 항목 | 단가 | 월 추정 |
|------|------|--------|
| Anthropic Max | 정액 | $200 |
| ChatGPT Pro (Codex) | 정액 | $200 |
| DeepSeek API (R&D B) | $0.27 in / $1.10 out | ~$5-10 |
| Google AI Studio (Tech Artist + dev-gemma) | free tier | $0 |
| **Voyage-3 embedding** | **$0.10/M** | **~$1-3** |
| Tavily search | $0.005/query | ~$5-10 |
| Qdrant Cloud (Phase 1) | free → $25 | $0~$25 |
| **합계** | | **~$420-500** |

Voyage-3는 매우 저렴 (1M 토큰 임베딩 = $0.10). KB가 완전히 비활성된 wiki 직접 호출 비용 대비 ROI 극히 높음.

## Phase 2 추가 절감

- Voyage-3 → BGE-M3 로컬 (-$3/월)
- Qdrant Cloud → 셀프호스트 (-$25/월)
- 추가: 전기료 ~+$15/월
- 순감 ~$13/월

## Source-Enforcement과의 정합

KB 청크는 항상 `source_url` + `citation`을 강제 포함 → LLM 답변에 자동 인용 → [[CLAUDE]]의 Source-Enforcement Pattern과 정합.

## Related

[[knowledge-db]] · [[qdrant-instance]] · [[orchestrator-protocol]]

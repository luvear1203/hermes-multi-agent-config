---
title: Continuous Research Loop — cron-based knowledge accumulation
created: 2026-05-10
updated: 2026-05-10
type: architecture
tags: [continuous-research, cron, multi-agent, knowledge-db]
sources:
  - "docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md"
confidence: high
---

# Continuous Research Loop

R&D Engineer A·B (`researcher` profile) operate in two modes: reactive (on-demand from Director) and cron (background accumulation). Cron mode adds proactive knowledge growth without user prompting. See [[roles]] for slot map and [[knowledge-db]] for storage layer.

## Cron Jobs (4)

Registered via `hermes cron create` (정확 schema, see Step 3 commits):

| Job | Schedule | Deliver | 역할 |
|---|---|---|---|
| `topic_crawl_daily` | `0 3 * * *` (매일 03:00) | local | arxiv (since=1d) + github (pushed=1d), max_results=5 per topic |
| `topic_crawl_weekly` | `0 4 * * 0` (일요일 04:00) | local | arxiv (7d) + semantic_scholar + github (7d) + tavily (broad) |
| `topic_curation_weekly` | `0 5 * * 6` (토요일 05:00) | telegram | Director가 토픽 노이즈/병합/리네임 후보 → 사용자 승인 카드 |
| `cost_report_weekly` | `0 18 * * 0` (일요일 18:00) | telegram | 주간 비용·토큰·KB 성장 리포트 |

Gateway 미실행이면 자동 fire 안 됨 → `hermes gateway install` 필요.

## Topic Lifecycle

1. **Auto-recommend** (`topic_recommender.py`): wiki tags + mythrill modules → top-N 후보 with score
2. **User approval** (HALT): Director가 후보 12개 제시 → 사용자가 등록할 N개 선택
3. **Register** (`kb_topic_register`): `topics` 컬렉션에 status=active로 등록
4. **Cron pickup**: 다음 daily/weekly 시점에 cron이 active topics 순회
5. **Curation** (weekly): 30일+ 비활동 = noise 후보, 의미 중복 = merge 후보, 모호한 이름 = rename 후보. 변경은 사용자 승인 필수

## Source-Enforcement

모든 cron-produced chunk는 `kb_tools.validate_payload` 통과 필수:
- 누락 `source_url`/`citation`/`content_hash` → discarded
- 중복 `content_hash` → skipped (idempotent re-runs)

## Routing (`crawl_loop.COLLECTION_BY_SOURCE`)

| Source | KB Collection |
|---|---|
| arxiv | kb_papers |
| semantic_scholar | kb_papers |
| github | kb_oss_projects |
| tavily | kb_dev_docs |

## 운영 제약 (현재 검증)

- Voyage Free TPM ~10K/min·~3 RPM: kb_upsert는 1요청씩, RPM 한도 내 운영
- arxiv free anonymous: IP throttle 빈번 (HTTP 500/429), `_get_with_backoff` 3 retries 후도 실패 가능. cron 다음 cycle에서 재시도 (transient 정책)
- semantic_scholar free anonymous: 동일 throttle 패턴
- github 무토큰: 60 req/hr (8 topics × daily = 8 req → 한도 내)
- tavily Free: 월 1000 query (weekly만 사용 → 4 × 8 topics × 4 sources × 5 results = 약 0.5K/월)

## 첫 검증 결과 (2026-05-10 daily crawl)

8 active topics × (arxiv + github) = 16 호출, total +31 chunks (모두 kb_oss_projects, arxiv 3건 transient 500). errors=8 (대부분 arxiv 500 + 일부 github 0 결과).

## Related

[[knowledge-db]] · [[orchestrator-protocol]] · [[multi-agent-system]] · [[roles]] · [[model-prompting-conventions]]

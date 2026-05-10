---
title: 설정 재구축 — 2026-05-10
created: 2026-05-10
updated: 2026-05-11
type: concept
tags: [rebuild, knowledge-db, multi-agent, audit, continuous-research]
sources:
  - "docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md"
  - "docs/superpowers/plans/2026-05-10-hermes-rebuild-and-knowledge-db.md"
confidence: high
---

# 설정 재구축 (2026-05-10 ~ 2026-05-11)

Hermes 운영 시스템의 무에서 유 재구축 + Knowledge DB 신설 + Continuous Researcher 가동의 의사결정 기록.

## 두 layer

- **지식 (wiki content)**: 보존 + 압축 (3 페이지). 폐기 0건.
- **설정 (config·profiles·auth·toolsets·cron·patches)**: 무에서 유.

## 주요 변경 (5 Step, 약 33 commits)

1. **Step 0 — Wiki Audit** (commits aa17c79 → 41c0d60): 66 페이지 분류 (preserve 35 / compress 3 / review 28). 사용자 결정 option_1_conservative.
2. **Step 1 — 설정 재구축 + Director Swap** (12 commits, 4b377c1 → d108b2c):
   - Director re-promoted: `claude-opus-4-7` via Anthropic Max OAuth (effort `xhigh`)
   - Sub-Director re-demoted: `gpt-5.5` via Codex OAuth (effort `high`)
   - 사유: "Opus 4.7 출력 품질 우선" (사용자 결정)
   - dev-gemma swap: `gemma-4-31b-it` → `claude-haiku-4-5-20251001` (Tier 1 paid에서도 16k TPM hard cap 회피)
   - Sub-Director 2회 review APPROVE
3. **Step 2 — Knowledge DB Phase 1** (6 commits, d6d3941 → aa0715e):
   - Qdrant Cloud GCP free tier + 12 컬렉션 (1024 dim cosine HNSW int8)
   - knowledge-db / research-external toolsets
   - Wiki-First → KB-Second hook (THRESHOLD 0.5)
   - 65 wiki + 1 mythrill .py + 1 smoke = 67 points 인덱싱
4. **Step 3 — Continuous Researcher cron + Topic Tracker** (7 commits, daae8a3 → a9b694f):
   - 4 cron jobs (정확 schema, prompt 기반): topic_crawl_daily/weekly, topic_curation_weekly, cost_report_weekly
   - Topic Tracker: 12 candidates → 사용자 승인 8 active topics
   - 첫 daily crawl: +31 chunks
   - Gateway dual-use op-fix: orchestrator profile 단독, jobs.json symlink
   - Sub-Director review APPROVE
5. **Step 4 — Wiki 압축 + graphify** (3 commits, ?? → ??):
   - 3 페이지 압축: 409 → 90줄 (-78%)
   - 원본 보존: `~/.hermes/wiki/raw/compressed_2026-05-10/`
   - graphify cluster-only: 246 nodes / 633 edges, 14 communities
   - KB 재임베딩: 압축 페이지 stale point 정리

## 운영 인프라 (정착)

- **Provider Path Discipline**: 모든 directing-grade는 OAuth only (API key 자동 전환 절대 금지). 적용 검증 완료.
- **Source-Enforcement**: 모든 KB 청크 `source_url` + `citation` + `content_hash` 강제. wiki 자체 갱신에도 적용 (1차 소스 cite, 자기 위반 자가 정정 사례 commit 074d86e).
- **Model-specific prompt format**: Claude=XML tags, GPT-5.5=7섹션 markdown headings. SoT는 [[model-prompting-conventions]].
- **Hermes Gateway dual-use**: orchestrator profile 단독 운영. global cron jobs.json symlink. macOS pmset (tcpkeepalive=1 / powernap=1 / 02:55 자동 wake) 정착.

## KB 최종 (Step 4 완료 시점)

| 컬렉션 | points |
|---|---|
| wiki_entities | 32 |
| wiki_concepts | 27 |
| wiki_architecture | 7 |
| mythrill_code | 1 |
| kb_papers | 1 |
| kb_oss_projects | 31 |
| topics | 8 |
| (kb_dev_docs, kb_industry_solutions, kb_lessons_learned, chat_memory, personal_notes) | 0 |
| **Total** | **107** |

cron이 시간이 지나면서 빈 컬렉션도 채울 예정 (kb_dev_docs는 weekly tavily, 나머지는 향후 source 추가).

## 다음 운용 시점

- **2026-05-12 03:00 KST**: 두 번째 daily crawl (자동)
- **2026-05-16 05:00 KST**: 첫 topic_curation_weekly (Telegram approval card)
- **2026-05-17 04:00 KST**: 첫 weekly broad crawl
- **2026-05-17 18:00 KST**: 첫 cost_report_weekly — Voyage usage + Anthropic Max + Codex Weekly + Tavily query 정량 보고

## Related

[[knowledge-db]] · [[continuous-research-loop]] · [[multi-agent-system]] · [[orchestrator-protocol]] · [[qdrant-instance]] · [[wiki-token-cost-reduction]] · [[model-prompting-conventions]]

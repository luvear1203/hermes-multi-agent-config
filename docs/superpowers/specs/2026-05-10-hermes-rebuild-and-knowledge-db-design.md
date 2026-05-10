# Hermes Settings Rebuild + Knowledge DB + Continuous Researcher — Design

**Date**: 2026-05-10
**Owner**: luvear1203
**Status**: Awaiting user spec review
**Supersedes**: `2026-05-10-hermes-multi-agent-stack-design.md` (initial greenfield brainstorm, deprecated)

---

## 0. 인지·전제 (반드시 spec 전체에 적용)

본 spec이 만드는 모든 변경은 다음 운영 규칙을 위반하지 않는다. 위반 시 즉시 수정.

| 규칙 | 출처 | 본 spec에서의 적용 |
|------|------|-------------------|
| **Provider Path Discipline — directing-grade는 OAuth only** | `wiki/CLAUDE.md`, `wiki/entities/hermes-max-integration.md` | Director·Sub-Director는 Anthropic Max OAuth + OpenAI Codex OAuth만. API key (`sk-ant-api*`, OpenAI API key) 절대 금지 |
| **Wiki-First → KB-Second → researcher debate** | `wiki/CLAUDE.md` | KB 검색은 wiki search miss 시 발동. 답변 인용은 wiki page 우선 |
| **Immediate-Reflection (4종 의무)** | `wiki/CLAUDE.md` | 변경마다 (1) `wiki/architecture/` 또는 `entities/` 갱신 (2) `log.md` 추가 (3) `updated:` 갱신 (4) 사용자 보고. 위반 시 protocol violation |
| **AI-to-AI English-only** | `wiki/CLAUDE.md` | LLM-facing 텍스트(worker prompts, delegate_task goal/context, system prompts)는 영어. 사용자↔AI는 한국어. log.md는 한국어 허용 |
| **Source-Enforcement Pattern** | `wiki/architecture/model-prompting-conventions.md` | KB 청크는 출처 페이로드 강제. R&D Engineer A·B에 `[SOURCE RULE] Every claim requires a source (URL/DOI). Discard responses without sources.` 유지 |
| **2-track**: 지식 = 보존+압축 / 설정 = 무에서 유 | 사용자 명시 (2026-05-10) | wiki content는 audit 후 보존/압축, `~/.hermes/{config.yaml,profiles/,auth.json,patches,cron}` 일체는 새로 생성 |

## 1. Goal

Hermes 운영 시스템을 **무에서 유로 재구축**하면서 다음을 동시에 달성한다.

1. **Director ↔ Sub-Director swap**: Director를 Claude Opus 4.7 (Anthropic Max OAuth)로, Sub-Director를 GPT-5.5 (OpenAI Codex OAuth)로 환원. 둘 다 구독 OAuth.
2. **Knowledge DB 신규 구축**: Qdrant 기반 의미 검색 인덱스. 1차 목적은 **wiki 탐색 시 토큰 비용 감소**. 2차 목적은 외부 자료 누적 + 출처 강제.
3. **Continuous Researcher 모드 신설**: R&D Engineer A·B에 cron 모드를 추가, 등록된 토픽에 대해 자동 누적.
4. **Wiki 보존 + 압축**: 기존 62 페이지 audit → 보존 / 압축 / 폐기 분류. 폐기는 사용자 승인 시만.
5. **설정 일체 재구축**: `config.yaml` 422줄, profiles 5개, auth, toolsets, cron, patches 모두 spec 기반으로 새로 정의.

## 2. Non-goals

- Mythrill 파이프라인 자체 코드 변경 X (`mythrill-pipeline/src/{bake,llm,overlay,sim,viewer}` 무관)
- C-Chasm IP 콘텐츠 변경 X (5 laws, 신의 세 유형, Azathoth 우주론은 SoT 그대로)
- AI Rookie 2026 컨테스트 마감 영향 작업 X
- Wiki concept/entity 자율 폐기 X (사용자 명시 외 보존)
- LLM 자체 학습/파인튜닝 X
- 외부 사용자 대상 서비스 X (단일 사용자)

## 3. 현재 상태 audit (Phase 0)

### 3.1 지식 audit — 62 페이지 분류 (잠정)

| 분류 | 대상 | 처리 |
|------|------|------|
| **보존 (그대로)** | architecture/* (5), c-chasm-ip-core, c-chasm-five-laws, mythrill-architecture, llm-separation-design, mpm-constitutive-equation-swap, three-deity-types, dual-ending-branch 등 SoT 페이지 | 변경 X. KB에는 인덱싱 |
| **압축 후보** | handoff 보고서, llm1-validation 검증 결과, mythrill-spike-01/02 후속 보고서 | dense form (요약 + 원본 링크) 변환. 원본은 `wiki/raw/`로 이동 |
| **폐기 후보** | (없음, 사용자 승인 시만) | 사용자 검토 |
| **신규 작성** | architecture/knowledge-db, architecture/continuous-research-loop, entities/qdrant-instance, concepts/wiki-token-cost-reduction, concepts/setting-rebuild-2026-05-10 | Phase 1 동시 작성 |

압축 후보의 dense form 변환 기준:
- LLM-facing instruction 페이지(architecture/*) — 영어, 250 단어 이하 권장
- 결과 보고 페이지(handoff/*, llm1-validation, spike-0X) — 헤더 표 + 핵심 발견 5줄 + 원본 링크
- IP/lore 페이지(C-Chasm 우주론, 신의 세 유형 등) — 보존 (내용 자체가 IP)

### 3.2 설정 audit — 무에서 유로 재구축 대상

| 파일/디렉토리 | 현재 상태 | 재구축 방향 |
|------------|----------|-----------|
| `~/.hermes/config.yaml` | 422줄, 일부 default값 그대로 | spec §4 기반으로 처음부터 재작성. providers 명시, fallback 명시 |
| `~/.hermes/profiles/orchestrator/` | gpt-5.5 / openai-codex / xhigh | **Director Opus 4.7 + Anthropic Max OAuth로 재정의** |
| `~/.hermes/profiles/sub-director/` | claude-opus-4-7 / anthropic | **Sub-Director GPT-5.5 + Codex OAuth로 재정의** |
| `~/.hermes/profiles/researcher/` | sonnet-4-5 default + deepseek override | dual-model 유지, SOUL.md 영어 유지 |
| `~/.hermes/profiles/tech-artist/` | gemma-4-31b-it / gemini | 그대로 유지 (Mythrill LLM ② 슬롯) |
| `~/.hermes/profiles/dev-gemma/` | gemma-4-31b-it / gemini (GCP 프로젝트 2) | 그대로 유지 |
| `~/.hermes/auth.json` | active_provider=openai-codex | **anthropic으로 swap, claude_code OAuth credential** |
| `~/.hermes/patches/` | anthropic_billing_bypass.py | 유지, 자동 cron 갱신도 유지 |
| `~/.hermes/cron/` | 빈 디렉토리 | spec §7 cron 4개 신규 정의 |
| `~/.hermes/bin/quota.sh` | 모델 인식 quota 보고 가동 | 유지, KB 인덱싱 비용 추적 추가 |
| `~/.hermes/sessions/` (DB) | hermes 세션 누적 | 유지, KB의 `chat_memory` 컬렉션과 동기 |
| `~/.hermes/wiki/graphify-out/` | 246 nodes / 633 edges / 14 communities | 유지, KB와 통합 (graphify 결과를 KB upsert) |

### 3.3 인프라 audit

- `kristianvast/hermes-claude-auth` bypass: 5종 패치 가동 중. **그대로 유지** (Provider Path Discipline 핵심 인프라)
- `kanban`: `dispatch_in_gateway: true`, dispatch_interval 60s. Local Agent Control Plane(Project 4)의 Mission Board와 통합 예정
- `model_catalog.url`: `https://hermes-agent.nousresearch.com/docs/api/model-catalog.json`. 그대로 유지

## 4. New Architecture (재정의)

### 4.1 역할 표 (확정안)

| Role | 모델 | 호출 경로 | 인증 |
|------|------|----------|------|
| **Director** | claude-opus-4-7 | `hermes chat` (default), `hermes chat --profile orchestrator` | Anthropic Max OAuth (claude_code keychain) + bypass 5종 |
| **Sub-Director** | gpt-5.5 | `hermes chat --profile sub-director` | OpenAI Codex OAuth (ChatGPT Pro) |
| **R&D Engineer A** | claude-sonnet-4-5-20250929 | `hermes chat --profile researcher` (default) | Anthropic Max OAuth |
| **R&D Engineer B** | deepseek-v4-pro | `hermes chat --profile researcher --provider deepseek -m deepseek-v4-pro` | DeepSeek API key (paid, $5-10/월 worker billing) |
| **Tech Artist** | gemma-4-31b-it | `hermes chat --profile tech-artist` | Google AI Studio free, GCP project 1, `GEMINI_API_KEY` |
| **Code Implementation** | gemma-4-31b-it | `hermes chat --profile dev-gemma` | Google AI Studio free, GCP project 2 (quota 분리) |
| **Validator** | non-LLM | scripts (`pytest`, regression runner) | — |
| **Engine Architect / Planner** | Director 겸직 | — | — |
| **Continuous Researcher** | R&D A·B (cron mode) | `hermes researcher crawl --mode {daily,weekly}` | 동일 |

### 4.2 Provider 매트릭스

```
Anthropic Max OAuth (claude_code keychain)
  ├── Director: claude-opus-4-7 (orchestrator profile)
  └── R&D Engineer A: claude-sonnet-4-5-20250929 (researcher default)

OpenAI Codex OAuth (ChatGPT Pro)
  └── Sub-Director: gpt-5.5 (sub-director profile, reasoning_effort: xhigh)

DeepSeek API (paid, ~$5-10/월)
  └── R&D Engineer B: deepseek-v4-pro (researcher --provider deepseek)

Google AI Studio (free tier)
  ├── Tech Artist: gemma-4-31b-it (GCP project 1)
  └── Code Implementation: gemma-4-31b-it (GCP project 2)

Voyage AI (paid, ~$1-3/월)
  └── Embedding (Phase 1): voyage-3 (1024 dim)

Qdrant Cloud (신규 billing surface, free → $25/월)
  └── Knowledge DB (Phase 1)
```

**중요**: directing-grade(Director, Sub-Director)에는 어떤 직접 API 경로도 들어가지 않는다. Anthropic API key·OpenAI API key는 auth.json·`.env` 어디에도 없다.

### 4.3 Auth 분배

| auth store | active_provider | credential |
|-----------|----------------|-----------|
| `~/.hermes/auth.json` | `anthropic` | claude_code OAuth (keychain 자동 검출) |
| `~/.hermes/profiles/orchestrator/auth.json` | `anthropic` | 동일 (전역 mirror) |
| `~/.hermes/profiles/sub-director/auth.json` | `openai-codex` | Codex OAuth (chat.openai.com OAuth credential 1개만) |
| `~/.hermes/profiles/researcher/auth.json` | `anthropic` (default) / `deepseek` (override) | claude_code OAuth + DeepSeek API key (별도 .env) |
| `~/.hermes/profiles/tech-artist/.env` | — | `GEMINI_API_KEY` (GCP project 1) |
| `~/.hermes/profiles/dev-gemma/.env` | — | `GEMINI_API_KEY` (GCP project 2) |

### 4.4 Toolsets (재정의)

기존:
- `hermes-cli` — terminal/file/git 기본
- `hermes-{telegram,discord,whatsapp,slack,signal,homeassistant,qqbot,yuanbao,teams}` — 메시저 어댑터
- `hermes-web-search`, `hermes-code-execution` — 활성화 권장

신규:
- **`research-external`** — arXiv·Semantic Scholar·GitHub·Tavily·Patent·Wayback·PDF extract (R&D A·B 전용)
- **`knowledge-db`** — Qdrant CRUD + dedupe + topic registry (모든 worker 공통)
- **`wiki-audit`** — wiki page 분류·압축 helper (Phase 0 도구, 1회용)

## 5. Director Swap 구체 절차 (8단계)

`wiki/architecture/orchestrator-protocol.md`의 "Adding a New Orchestrator Profile" 5단계 + Immediate-Reflection 4종 = 8단계 + 검증.

### Step 1: config.yaml swap
```yaml
# ~/.hermes/config.yaml (root level)
model:
  default: claude-opus-4-7        # was: gpt-5.5
  provider: anthropic             # was: openai-codex
  base_url: https://api.anthropic.com  # OAuth + bypass로 호출됨, API key 아님
agent:
  reasoning_effort: medium        # Opus는 xhigh 미지원, medium/high
```

### Step 2: orchestrator profile config 동일 변경
`~/.hermes/profiles/orchestrator/config.yaml` 동일 model 블록.

### Step 3: sub-director profile config swap
```yaml
# ~/.hermes/profiles/sub-director/config.yaml
model:
  default: gpt-5.5
  provider: openai-codex
  base_url: https://chatgpt.com/backend-api/codex
agent:
  reasoning_effort: xhigh
```

### Step 4: auth.json swap
```bash
# 전역 + orchestrator
jq '.active_provider = "anthropic"' ~/.hermes/auth.json
jq '.active_provider = "anthropic"' ~/.hermes/profiles/orchestrator/auth.json

# sub-director: Codex credential을 active로 (이미 store에 있음, active만 swap)
jq '.active_provider = "openai-codex"' ~/.hermes/profiles/sub-director/auth.json
```
**삭제 없음**. credential pool에 두 종 모두 유지, active_provider만 swap.

### Step 5: wiki architecture 갱신
- `wiki/architecture/roles.md` — Director/Sub-Director 행 swap, Reason 갱신 ("사용자 결정 2026-05-10: ...")
- `wiki/architecture/orchestrator-protocol.md` — "Director Routing" 섹션 swap, 날짜 갱신
- `wiki/architecture/cost-tiers.md` — Tier 1 후보 로스터 정렬

### Step 6: CLAUDE.md "Director Routing" 섹션 swap
`wiki/CLAUDE.md` "## Director Routing (2026-05-07c)" → "## Director Routing (2026-05-10)"로 swap, 본문 swap.

### Step 7: entities/multi-agent-system.md swap
다이어그램 + Active Profiles 표 + History 행 추가.

### Step 8: log.md 신규 항목 + updated 갱신 + 검증
```
## [2026-05-10X] decide | Director ↔ Sub-Director re-swap (Opus 4.7 promoted, GPT-5.5 demoted)
- 결정: Director = claude-opus-4-7 via Anthropic Max OAuth. Sub-Director = gpt-5.5 via Codex OAuth.
- 사유: 사용자 결정. 구체 사유는 §13 위험·미결 사항 1번 참조 (spec user review 시 확정).
- 운영 제약: 두 구독 모두 활성. 두 OAuth 한도 동시 운영. quota.sh가 active provider만 보고하므로 sub-director 호출 후에는 별도 확인 필요.
- wiki 갱신: roles, orchestrator-protocol, cost-tiers, CLAUDE.md, multi-agent-system, log.md
- 검증: hermes status, smoke test 5종 (default, orchestrator, sub-director, researcher A·B, tech-artist, dev-gemma)
- graphify 갱신 필요 (다음 증분 사이클).
```

검증:
```bash
hermes status                                                    # Model=opus-4-7
hermes chat -q 'say ok' --max-turns 1 -t '' -Q                  # ok
hermes chat --profile orchestrator -q 'say ok' --max-turns 1 -t '' -Q   # ok
hermes chat --profile sub-director -q 'say ok' --max-turns 1 -t '' -Q   # ok
hermes chat --profile researcher -q 'say ok' --max-turns 1 -t '' -Q     # ok (sonnet-4-5)
hermes chat --profile researcher --provider deepseek -m deepseek-v4-pro -q 'say ok' --max-turns 1 -t '' -Q   # ok
hermes chat --profile tech-artist -q 'say ok' --max-turns 1 -t '' -Q    # ok
hermes chat --profile dev-gemma -q 'say ok' --max-turns 1 -t '' -Q      # ok
```

## 6. Knowledge DB (Qdrant)

### 6.1 인스턴스 (Phase 1)

- **Phase 1**: Qdrant Cloud free tier → 사용량 증가 시 $25/월 (1GB RAM, 4GB storage). 신규 billing surface로 사용자 승인 게이트 통과(본 spec).
- **Phase 2**: Mac Studio M5 Ultra 또는 DGX Spark 도착 후 Qdrant 셀프호스트 (도커). Snapshot export/import로 마이그레이션.

### 6.2 컬렉션 12개

각 컬렉션 1024 dim, cosine distance, HNSW 인덱스, scalar quantization.

| 컬렉션 | 자료 | 차원 | 핵심 페이로드 추가 필드 |
|--------|------|------|--------------------|
| `wiki_entities` | wiki/entities/ 임베딩 | 1024 | wiki_path, wikilinks[], type, confidence |
| `wiki_concepts` | wiki/concepts/ 임베딩 | 1024 | wiki_path, wikilinks[], type |
| `wiki_architecture` | wiki/architecture/ 임베딩 | 1024 | wiki_path, wikilinks[], type |
| `kb_papers` | arXiv·Semantic Scholar | 1024 | doi, arxiv_id, authors[], year, venue, abstract, pdf_url |
| `kb_oss_projects` | GitHub/GitLab | 1024 | repo_url, stars, last_commit, license, language, status |
| `kb_industry_solutions` | 상용 제품·특허 | 1024 | company, product, patent_id, summary |
| `kb_lessons_learned` | 폐기/실패 프로젝트 | 1024 | repo_url, abandonment_reason, post_mortem_url |
| `kb_dev_docs` | Unreal·SO·MDN 등 | 1024 | source_url, version, doc_type |
| `mythrill_code` | mythrill-pipeline/src/ | 1024 | file_path, module, language, last_modified |
| `chat_memory` | hermes 세션 누적 | 1024 | session_id, profile, timestamp, tier |
| `personal_notes` | wiki/raw/obsidian-vault/Brain/ | 1024 | vault_path, tags[] |
| `topics` | 추적 토픽 마스터 | — (메타만) | name, description, keywords[], status, last_crawled, crawl_freq |

### 6.3 강제 페이로드 (모든 컬렉션 공통)

```json
{
  "source_url": "string",                // 필수
  "content_hash": "sha256:...",          // dedupe 키
  "retrieved_at": "ISO8601",
  "citation": "Markdown citation string",
  "relevance_topics": ["topic_id_1", ...],
  "language": "en|ko|...",
  "embedding_model": "voyage-3|bge-m3",
  "confidence": "high|medium|low"        // wiki frontmatter 정합
}
```

답변 생성 시 KB 청크의 `citation` 필드를 LLM에 함께 전달 → 답변에 출처 자동 포함 (Source-Enforcement Pattern과 정합).

### 6.4 Embedding 정책

- **Phase 1**: Voyage-3 (1024 dim, paid ~$0.10/M tokens, Anthropic 추천 한·영 다국어)
- **Phase 2**: BGE-M3 (1024 dim, 로컬 무료, 8192 토큰 입력, dense+sparse 동시) — AI 머신 도착 후 재임베딩

차원 동일하므로 컬렉션 schema 변경 없이 재임베딩만으로 전환.

### 6.5 graphify 통합

`wiki/graphify-out/`의 semantic 추출 결과(246 nodes / 633 edges)는 cron으로 KB upsert.

```
graphify cluster-only wiki --no-viz   # 로컬 graph 갱신
graphify check-update wiki            # pending flag 확인
└── (변경 있으면) /graphify wiki --update    # LLM semantic extraction (Sonnet/Opus quota 필요)
└── KB 동기화 스크립트 → wiki_entities/concepts/architecture upsert
```

### 6.6 Wiki-First → KB-Second 검색 hook

```
사용자 질문 → orchestrator
            ↓
          Wiki search (graphify graph traversal, cheap)
            HIT → Wiki page 인용 답변
            MISS → KB search (Qdrant cosine top-k)
                    HIT → KB chunk 인용 답변 + wiki SoT crosslink
                    MISS/부족 → researcher debate (R&D A·B)
                                → KB upsert + wiki 신규 페이지 후보 보고
```

이 hook은 `~/.hermes/patches/`에 새 패치 또는 신규 toolset(`knowledge-db`)으로 구현.

## 7. Continuous Researcher

### 7.1 cron 작업 4개 (`~/.hermes/cron/`)

```yaml
# topic_crawl_daily — 매일 03:00
schedule: "0 3 * * *"
command: hermes researcher crawl --mode daily
description: |
  topics 컬렉션의 active 토픽 순회.
  arXiv submittedDate=NOW-1d, GitHub pushed:>=NOW-1d, HN 검색.
  결과 → 해당 컬렉션에 인덱싱 (dedupe + Source-Enforcement)

# topic_crawl_weekly — 매주 일요일 04:00
schedule: "0 4 * * 0"
command: hermes researcher crawl --mode weekly
description: |
  광범위 검색. Patent, archive.org, GDC, awesome-lists.
  oss_projects의 last_commit/stars 갱신, dormant 자동 라벨.

# topic_curation_weekly — 매주 토요일 05:00
schedule: "0 5 * * 6"
command: hermes researcher curate-topics
description: |
  orchestrator(Opus)가 topics 마스터 재검토.
  noise 후보 / 통합 후보 / rename 후보 → Telegram 카드 → 사용자 승인.

# cost_report_weekly — 매주 일요일 18:00
schedule: "0 18 * * 0"
command: hermes report cost --period 7d --notify telegram
description: |
  sessions DB + provider별 토큰 분포 + KB hit rate + dedupe rate + 외부 호출 횟수.
  Telegram 리포트 + log.md 항목 추가.
```

### 7.2 Topic Tracker

**자동 추천 + 사용자 승인** (사용자 답변 2026-05-10).

- 추천 입력: mythrill-pipeline 모듈명/주석, wiki concepts/entities tags, 최근 N개 chat_memory
- 출력: Telegram 카드 (또는 Mission Board MVP 도착 후 dashboard)
- 사용자 승인 시 `topics` 컬렉션 등록 + cron 크롤 활성

기본 default 토픽 후보 (Mythrill·C-Chasm 컨텍스트):
- `mpm_constitutive_swap`, `taichi_mpm`, `vfx_baking_flipbook_vat`, `niagara_vfx`, `enhanced_input_system`, `cosmic_horror_design`, `unreal_optimization`, `level_streaming`, `nl_to_si_parameter`, `llm_pipeline_validation`

### 7.3 R&D Engineer A·B의 모드 확장

기존 reactive 모드 + 신규 cron 모드.

```python
# hermes researcher crawl --mode daily 호출 시 내부 흐름 (영어, AI-to-AI)
def daily_crawl():
    topics = qdrant.scroll("topics", filter={"status": "active"})
    for topic in topics:
        # R&D A (Sonnet 4.5)
        new_papers = arxiv_search(topic.keywords, since="1d")
        new_repos = github_search(topic.keywords, pushed=">=1d")
        # R&D B (DeepSeek V4) cross-validates
        deduped = research_b_dedupe(new_papers + new_repos, topic)
        for chunk in deduped:
            assert chunk.source_url and chunk.content_hash and chunk.citation
            qdrant.upsert(chunk.collection, chunk)
        topic.last_crawled = now()
```

### 7.4 SOUL.md 영어 강제

R&D A·B의 SOUL.md는 영어 (이미 적용). cron 모드 추가 시:

```markdown
# R&D Engineer (cron mode addition)

When invoked with --mode daily|weekly:
- Read topics collection. For each active topic:
- Execute external search via research-external toolset.
- Apply Source-Enforcement: every chunk MUST carry source_url, citation, content_hash.
- Apply dedupe: skip on content_hash hit, only update retrieved_at.
- Upsert to the appropriate kb_* collection.
- Append a line to ~/.hermes/wiki/log.md (Korean OK):
  `## [YYYY-MM-DD] crawl | <topic> | <N> new chunks across <M> collections`

Forbidden:
- Direct API path switches (use hermes-managed credentials only).
- Modifying wiki content (read-only). Only orchestrator commits writes.
- Korean in worker-facing output. JSON or English markdown only.
```

## 8. Wiki 압축·정리 정책

### 8.1 dense form 변환 대상

| 페이지 | 현재 | 압축 후 |
|--------|------|---------|
| handoff/* | 검증 보고서 (수천 단어) | 헤더 표 + 5줄 핵심 발견 + 원본 링크 (`raw/handoff_archive/`로 이동) |
| llm1-validation entity | 50입력 검증 결과 상세 | 정확도 표 + v1→v3 evolution 5줄 + 원본 링크 |
| spike-01/02 entity | 보고서 | 동일 패턴 |
| log.md (오래된 부분) | 누적 chronological | 분기별 archive 분리 (예: `log/2026-Q1.md`, `log/2026-Q2.md`) |

### 8.2 그대로 보존 (절대 변경 X)

- C-Chasm IP 페이지 전부 (c-chasm-ip-core, five-laws, 신의 세 유형, 강림형/회귀형/광기형, 매크로 팩션 구조 등)
- Mythrill architecture·llm-separation·mpm-constitutive-equation-swap·trigger-classification 등 SoT 개념
- architecture/* 모든 페이지

### 8.3 폐기 (사용자 명시 시만)

자동 폐기 X. 본 spec에서 폐기 후보 목록을 제시하지 않음. Continuous Researcher의 weekly curation에서 noise 토픽이 발견되면 사용자 승인 후 archive (삭제 아님).

### 8.4 graphify 재실행

압축 작업 후:
```bash
graphify check-update wiki
/graphify wiki --update         # LLM semantic extraction, Opus quota 사용
graphify cluster-only wiki --no-viz
```
KB의 `wiki_entities`, `wiki_concepts`, `wiki_architecture` 컬렉션 재임베딩.

## 9. 신규 wiki 페이지 (Phase 1 동시 작성)

| 페이지 | 위치 | 내용 요약 |
|--------|------|---------|
| `architecture/knowledge-db.md` | wiki/architecture/ | KB 정의·정책·12 컬렉션·페이로드 강제·Wiki-First → KB-Second hook |
| `architecture/continuous-research-loop.md` | wiki/architecture/ | cron 4개·Topic Tracker·R&D A·B mode 확장·Source-Enforcement 정합 |
| `entities/qdrant-instance.md` | wiki/entities/ | Phase 1 Cloud → Phase 2 셀프호스트 인스턴스 운영 |
| `concepts/wiki-token-cost-reduction.md` | wiki/concepts/ | KB 도입의 1차 가치 메커니즘·정량 측정 |
| `concepts/setting-rebuild-2026-05-10.md` | wiki/concepts/ | 본 spec의 무에서 유 재구축 의사결정 기록 |

각 페이지 frontmatter 표준:
```yaml
---
title: <Title>
created: 2026-05-10
updated: 2026-05-10
type: architecture | entity | concept
tags: [knowledge-db, multi-agent, ...]
sources: ["docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md"]
confidence: medium
---
```

## 10. Wiki Maintenance Loop 정합

`orchestrator-protocol.md`의 Wiki Maintenance Loop와 통합. 본 spec 구현 중 모든 변경에 4종 의무 적용:

1. 변경 발생 → `wiki/architecture/` 또는 `entities/` 페이지 신규/갱신
2. `wiki/log.md`에 `## [YYYY-MM-DD] <action> | <subject>` 블록 추가 (한국어 허용)
3. 모든 수정 페이지 `updated:` 오늘로 갱신
4. 사용자 보고 (Telegram 또는 직접 응답)

위 4개 누락 = protocol violation. 본 spec 구현 plan에 검증 step 포함.

## 11. 비용 추정 (월 단위, 사용자 답변 2026-05-10 기반)

| 항목 | 단가 / 정액 | 월 비용 |
|------|------------|--------|
| Anthropic Max | 정액 | $200 |
| ChatGPT Pro (Codex) | 정액 | $200 |
| DeepSeek API (R&D B) | $0.27 in / $1.10 out | ~$5-10 |
| Google AI Studio (Tech Artist + dev-gemma) | free tier | $0 |
| Voyage-3 embedding | $0.10/M | ~$1-3 |
| Tavily search | $0.005/query | ~$5-10 |
| SerpAPI (선택) | — | $0~$50 |
| Qdrant Cloud (Phase 1) | free → $25 | $0~$25 |
| **합계** | | **~$420-500 (약 55-65만원)** |

사용자 명시(2026-05-10) "두 구독 모두 활성, 외부 API 포함 ~55-60만원" 가정과 정합.

Phase 2 (AI 머신 도착 후) 변동:
- Voyage-3 → BGE-M3 로컬 (-$3)
- Qdrant Cloud → 셀프호스트 (-$25)
- 추가: 전기료 ~$15
순감 약 ~$13/월.

## 12. 도입 단계 (5 Step)

각 Step은 별도 Phase로 분리, 각각 검증 게이트.

### Step 0: Wiki Audit (1일)
- 62 페이지 분류표 작성 (보존/압축/폐기 후보)
- 사용자 검토 후 압축 대상 확정
- graphify check-update + cluster-only

### Step 1: 설정 무에서 유 재구축 (1일)
- `~/.hermes/{config.yaml,profiles/*,auth.json,cron/*,patches/*}` 새로 작성
- Director Swap §5 8단계 실행
- smoke test 5종 통과 확인
- wiki Immediate-Reflection 4종 적용

### Step 2: Knowledge DB Phase 1 (2일)
- Qdrant Cloud 가입 (사용자 승인 게이트)
- 12 컬렉션 생성 (스키마 §6.2)
- Voyage API key 등록 (`.env`)
- 신규 toolset `knowledge-db`, `research-external` 구현
- Wiki 인덱싱 첫 패스 (62 페이지 → wiki_entities/concepts/architecture)
- mythrill-pipeline/src/ 인덱싱 첫 패스
- Wiki-First → KB-Second hook 활성

### Step 3: Continuous Researcher cron + Topic Tracker (2일)
- cron 4개 등록
- Topic Tracker 추천 → 사용자 승인 → topics 컬렉션 등록
- daily/weekly 첫 실행 dry-run

### Step 4: Wiki 압축 + graphify 재실행 (1일)
- Step 0 분류 결과 따라 dense form 변환
- raw/ 아카이브 이동
- /graphify wiki --update (Opus quota 사용, GREEN 시점)
- KB 재임베딩

### 총 7일 (병렬 실행 가능 부분 있음, 단축 가능)

각 Step 끝에 **검증 게이트**: smoke test + Wiki Maintenance Loop 4종 + cost report.

## 13. 위험·미결 사항

| 항목 | 위험 | 완화 |
|------|------|------|
| Director re-swap 사유 | 2026-05-07b 결정과 정반대 | spec 작성 시 사용자에게 사유 추가 받아 log.md에 기록 |
| 두 구독 동시 한도 | Opus·GPT-5.5 동시 호출 시 양쪽 quota 동시 소진 | quota.sh를 양쪽 active 시 둘 다 보고하도록 확장. Sub-Director 호출 후 quota 별도 체크 |
| Knowledge DB billing 증가 | Qdrant Cloud 사용량이 free tier 초과 | weekly cost_report에서 KB 사용량 라인 추가, 임계점 알람 |
| AI Rookie 2026 마감 영향 | 본 spec 구현 7일이 마감과 겹침 | Step 0·1만 마감 전 적용, Step 2~4는 마감 후 |
| Wiki 압축 정보 손실 | dense form 변환 시 컨텍스트 손실 | 원본은 raw/ 보존, 항상 link 유지. graphify 재실행으로 그래프 무결성 검증 |
| Voyage API 종속 | 회사 정책 변경 시 임베딩 재계산 | Phase 2 BGE-M3 이주 계획 (1024 dim 동일) |
| KB hit rate 미달 | wiki·KB 모두 miss 시 외부 호출 폭증 | researcher debate fallback, weekly curation으로 토픽 갱신 |
| sessions DB ↔ chat_memory 컬렉션 동기 | 중복·드리프트 가능 | sessions DB를 SoT, KB는 인덱스로 단방향 |

## 14. 성공 기준

- Director Swap: hermes status `claude-opus-4-7` 확인, smoke test 8종 모두 통과
- 모든 profile config·auth·toolset이 spec과 1:1 일치 (audit 스크립트 통과)
- KB Phase 1: wiki 62 페이지 + mythrill src 100% 인덱싱
- 토큰 절감: KB·wiki 압축 도입 후 30일 평균 입력 토큰 30% 이상 감소 (sessions DB 비교)
- wiki 탐색 토큰: 동일 질문에 대한 평균 wiki 검색 토큰 50% 이상 감소
- Continuous Researcher: 매주 새 자료 50건 이상 누적, 4종 이상 source 다양성
- Wiki Maintenance Loop 위반 0건 (감사 가능, log.md에 4종 entry 매번 확인)
- Provider Path Discipline 위반 0건 (auth.json·.env에 API key 없음)
- Phase 1 월 비용 ~$420-500 범위 내
- AI Rookie 2026 마감 일정 영향 0

## 15. 다음 단계

본 spec 사용자 승인 후 `superpowers:writing-plans` 스킬을 호출하여 5-step 단계별 구현 plan을 작성한다.

Phase 2 (AI 머신 도착 후 셀프호스트 마이그레이션)는 머신 결정·도착 시점에 별도 spec(`2026-XX-XX-hermes-phase2-local-migration-design.md`)으로 분리.

> **DEPRECATED 2026-05-10** — replaced by [`2026-05-10-hermes-rebuild-and-knowledge-db-design.md`](./2026-05-10-hermes-rebuild-and-knowledge-db-design.md). Initial brainstorm assumed greenfield setup; the new spec correctly accounts for the existing 5-profile / 9-role Hermes runtime, OAuth-only directing-grade routing, wiki SoT, Mythrill VFX-pipeline reality, and AI Rookie 2026 contest constraints.

# Hermes Multi-Agent Stack with Continuous Knowledge Curator — Design

**Date**: 2026-05-10
**Owner**: luvear1203
**Status**: DEPRECATED — superseded

---

## 1. Goal

Hermes Agent (Nous Research) 위에서 운용하는 **다용도 멀티 에이전트 + 자동 누적형 지식 DB** 시스템을 구축한다. 핵심은 두 가지:

1. **Vector DB로 토큰 비용을 정량적으로 줄인다** — 매번 풀 컨텍스트를 LLM에 보내지 않고, 벡터 검색으로 정확한 청크만 주입한다. 입력 토큰 30~50% 감소를 목표로 한다.
2. **Researcher 에이전트가 백그라운드에서 지식을 계속 축적한다** — 등록된 프로젝트 토픽(물리·신화·AI·렌더링 등)에 대해 논문·오픈소스·상용 제품·실패 사례를 자동으로 크롤링·인덱싱한다. 모든 자료는 출처 강제 포함.

단일 솔로 개발자가 게임 개발·코딩·리서치·일상 비서 작업 모두를 하나의 게이트웨이로 처리한다.

## 2. Use Cases (우선순위 순)

1. **Unreal 게임 개발 보조** — `mythrill-pipeline` C++/Blueprint 코드, 에셋 명명, 신화 자료 리서치, 스토리 검증, 시네마틱 기획
2. **일반 코딩/엔지니어링** — 멀티 프로젝트 코드 작성·리뷰·디버깅·자동화
3. **리서치 + 지식 관리** — Obsidian·신화/논문·오픈소스 자료 정리, 노트 통합 검색, 장기 메모리 누적
4. **다용도 일상 비서** — Telegram/Discord 연동, 이메일·일정·잡무, 크론 작업

## 3. Non-Goals

- 자체 LLM 학습·파인튜닝 (Hermes 4는 Nous 공식 가중치만 사용)
- 외부 사용자 대상 서비스 (개인용 단일 사용자)
- Unreal 인게임 NPC AI (게임 코드 측 별도 처리)
- 상용 제품·특허 자료의 무단 재배포 (개인 학습·참조 용도로만 인덱싱)

## 4. Architecture

### 4.1 Phase 1 — 클라우드 풀스택 (지금 ~ AI 머신 도착)

```
┌────────────────────────────────────────────────────────┐
│  M1 Air (게이트웨이 머신, 8GB)                            │
│  Hermes Agent CLI / Telegram                          │
└────────────────────────────────────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────┐
│  Orchestrator: Claude Opus 4.7 (anthropic, max think) │
│   - 사용자 의도 해석, 작업 분할, 깊은 추론                  │
└────────────────────────────────────────────────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ Code    │   │ Light    │   │ Researcher│  │ Cheap    │
  │ Sonnet  │   │ Haiku    │   │ Sonnet 4.6│  │ DeepSeek │
  │ 4.6     │   │ 4.5      │   │ + tools  │   │ V4 (fbk) │
  └─────────┘   └──────────┘   └──────────┘   └──────────┘
                                     │
                                     ▼
       ┌──────────────────────────────────────────────┐
       │  외부 검색 도구 (researcher 전용 toolset)        │
       │  - arXiv API, Semantic Scholar API           │
       │  - GitHub Search API, GitLab Search           │
       │  - Google Scholar (via SerpAPI), Tavily      │
       │  - Patent (Google Patents), Hacker News API  │
       │  - archive.org (Wayback)                     │
       └──────────────────────────────────────────────┘
                                     │
                                     ▼
       ┌──────────────────────────────────────────────┐
       │  Embedding: Voyage-3 (voyageai, 1024 dim)    │
       └──────────────────────────────────────────────┘
                                     │
                                     ▼
       ┌──────────────────────────────────────────────┐
       │  Vector DB: Qdrant Cloud (free → $25 plan)   │
       │  10개 컬렉션 (§5.2)                            │
       └──────────────────────────────────────────────┘
```

### 4.2 Phase 2 — 진짜 하이브리드 (AI 머신 도착 후, 2026 하반기)

```
M1 Air (게이트웨이)              AI 머신 (Mac Studio M5 Ultra 또는 DGX Spark)
└── Hermes Agent                ├── vLLM 또는 LM Studio
    ├── Orchestrator           │   ├── Hermes 4 70B (FP8/Q4)  ← Nous 자체 모델
    │   = Claude Opus 4.7      │   ├── Qwen3-Coder-30B (코드 전담)
    │     (클라우드 유지)         │   └── Llama-4-Scout-17B-MoE (researcher 보조)
    │                          ├── Qdrant 셀프호스트 (도커, 6333)
    ├── 로컬 위임 라우팅         │   - 10개 컬렉션
    │   - light → Hermes 4     ├── BGE-M3 임베딩 (한/영 다국어, 1024 dim)
    │   - code → Qwen3-Coder   ├── (선택) Tika/Unstructured (PDF·논문 파싱)
    │   - researcher → Llama 4 │   
    │                          └── Tailscale로 M1 Air ↔ AI 머신 사설망
    │
    ├── 클라우드 fallback       
    │   = DeepSeek V4 / Gemini 2.5 Flash
    │
    └── Cron 작업 (매일/매주)
        → continuous researcher → AI 머신 LLM 호출
```

**원칙**: 깊은 추론·플래닝은 클라우드 Opus 4.7. 분류·요약·코드 분석·외부 검색·임베딩은 로컬. RAG와 임베딩은 모두 로컬.

## 5. Knowledge DB (Vector DB) 설계

### 5.1 Qdrant 선정 근거

- Rust 기반, 활발한 발전, 도커 한 줄 셋업
- 강력한 페이로드 필터링 (zone, project, status 등 다중 조건)
- 멀티 컬렉션·네임스페이스로 도메인 분리
- 셀프호스트 + SaaS 양쪽 지원 → Phase 1 → Phase 2 전환 자연스러움
- HNSW 인덱스, scalar/binary quantization으로 메모리 효율
- Snapshot export/import로 마이그레이션 쉬움

### 5.2 컬렉션 (10개)

| 컬렉션 | 자료 | 핵심 페이로드 |
|--------|------|--------------|
| `topics` | 추적 중인 프로젝트 토픽 마스터 | name, description, keywords[], status, created_at, last_crawled, crawl_freq |
| `papers` | arXiv·Semantic Scholar 논문 | doi, arxiv_id, title, authors[], year, venue, abstract, pdf_url |
| `oss_projects` | GitHub/GitLab 오픈소스 | repo_url, stars, last_commit, license, language, status (active/archived/abandoned) |
| `industry_solutions` | 상용 제품·특허 | company, product, patent_id, summary |
| `lessons_learned` | 폐기/실패 프로젝트 | repo_url, abandonment_reason, post_mortem_url, key_findings |
| `dev_docs` | Unreal·Stack Overflow·MDN 등 | source_url, version, language, doc_type |
| `game_lore` | 신화·원전설 | mythology_source (Egyptian/Greek/Norse...), zone, faction, character |
| `game_code` | mythrill-pipeline 자체 | repo, file_path, module, language, last_modified |
| `personal_notes` | Obsidian Vault | vault_path, tags[], updated_at |
| `chat_memory` | Hermes 대화 누적 | session_id, user, timestamp, tier (working/long_term) |

### 5.3 모든 컬렉션 공통 강제 페이로드

```json
{
  "source_url": "https://...",            // 필수
  "content_hash": "sha256:...",           // dedupe 키
  "retrieved_at": "2026-05-10T12:00:00Z", // ISO8601
  "citation": "Smith et al. (2024)...",   // Markdown 형식 인용
  "relevance_topics": ["alchemy_physics","boss_ai"],
  "language": "en|ko|...",
  "embedding_model": "voyage-3|bge-m3"
}
```

답변 생성 시 RAG 컨텍스트의 모든 청크는 `citation` 필드를 함께 LLM에 전달 → 답변에 출처 자동 인용 강제.

### 5.4 Dedupe 전략

- 인덱싱 전 `content_hash` 조회 → 존재하면 skip (또는 `retrieved_at`만 갱신)
- arXiv·DOI 등 고유 ID가 있으면 `payload_id`로 사용
- Re-indexing 정책: paper은 영구 보존, oss_projects의 README는 월 1회 갱신, dev_docs는 분기별 갱신

### 5.5 임베딩 모델

- **Phase 1: Voyage-3** (1024 dim) — 한·영 다국어 RAG 우수, Anthropic 공식 추천
- **Phase 2: BGE-M3** (1024 dim) — 다국어, 8192 토큰 입력, dense+sparse 동시, 로컬 무료
- 두 모델 모두 1024 차원이라 컬렉션 스키마 변경 없이 재임베딩으로 전환 가능
- 다국어 검색을 위해 텍스트 정규화 후 임베딩 (사용자 노트는 한국어, 논문은 영어 혼재)

## 6. Researcher 에이전트 — 두 모드

### 6.1 모드 A: On-demand researcher

사용자 질문 → orchestrator → vector DB 검색 → 결과 부족 시 researcher 호출.

```
def handle_query(q):
    chunks = qdrant.search(q, top_k=20)
    if relevance_score(chunks) < THRESHOLD:
        new_chunks = researcher.search_external(q)
        qdrant.upsert(new_chunks)            # dedupe 자동 적용
        chunks = qdrant.search(q, top_k=20)  # 재검색
    return orchestrator.answer(q, context=chunks)
```

### 6.2 모드 B: Continuous researcher (cron)

`hermes-multi-agent-config/cron/` 디렉토리에 작업 정의.

**작업 1: `topic_crawl_daily`** (매일 03:00)
- `topics` 컬렉션의 모든 active 토픽 순회
- 각 토픽에 대해:
  - arXiv: `submittedDate:[NOW-1day TO NOW]` 신규 논문
  - GitHub: `pushed:>=NOW-1d sort:stars` 신규/갱신 repo
  - Hacker News: 검색 키워드 매치 스토리
- 결과 → 해당 컬렉션에 인덱싱 (출처·hash 강제)

**작업 2: `topic_crawl_weekly`** (매주 일요일 04:00)
- 더 광범위 검색: Patent, archive.org, GDC talks, awesome-lists
- 기존 oss_projects의 last_commit·stars 갱신, 6개월 이상 commit 없으면 status를 `dormant`로

**작업 3: `topic_curation_weekly`** (매주 토요일 05:00)
- Orchestrator가 `topics` 마스터 재검토
- 노이즈 토픽 후보 / 통합 후보 / rename 후보 보고서 → Telegram 푸시
- 사용자 승인 시 반영

**작업 4: `cost_report_weekly`** (매주 일요일 18:00)
- Sessions DB에서 토큰 사용량 집계
- RAG hit rate, dedupe rate, 외부 호출 횟수
- Telegram 리포트

### 6.3 Topic 등록 — 자동 추천 + 사용자 승인

1. Orchestrator가 다음을 분석해 토픽 후보 추출:
   - mythrill-pipeline 코드 (모듈명·주석)
   - Obsidian Vault (자주 등장하는 태그)
   - 최근 N개 chat_memory (사용자가 자주 묻는 도메인)
2. 후보를 Telegram에 카드 형태로 전송 → 사용자가 승인/거부/이름 수정
3. 승인된 토픽만 `topics` 컬렉션에 등록되고 cron 크롤 대상이 됨

기본 default 토픽 후보 (사용자 프로젝트 기반 자동 제안 예시):
- `alchemy_physics`, `cinematic_boss_ai`, `egyptian_mythology`, `greek_mythology`, `unreal_optimization`, `niagara_vfx`, `level_streaming`, `enhanced_input_system`

## 7. config.yaml 변경 사항 (Phase 1)

```yaml
model:
  default: claude-opus-4-7         # was: deepseek-v4-pro
  provider: anthropic
  base_url: https://api.anthropic.com

providers:
  anthropic:
    api_key_env: ANTHROPIC_API_KEY
  deepseek:
    api_key_env: DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com
  voyageai:
    api_key_env: VOYAGE_API_KEY
  qdrant:
    url_env: QDRANT_URL
    api_key_env: QDRANT_API_KEY

fallback_providers:
  - deepseek

agent:
  reasoning_effort: high            # was: medium
  service_tier: priority            # was: ''

prompt_caching:
  cache_ttl: 1h                     # was: 5m

compression:
  enabled: true
  threshold: 0.7                    # was: 0.5
  target_ratio: 0.5                 # was: 0.2 (정보 손실 절반으로)
  protect_last_n: 30                # was: 20

delegation:
  model: claude-haiku-4-5
  provider: anthropic
  inherit_mcp_toolsets: true
  reasoning_effort: medium
  routes:
    code:        { model: claude-sonnet-4-6 }
    researcher:  { model: claude-sonnet-4-6, toolsets: [research-external] }
    light:       { model: claude-haiku-4-5 }

auxiliary:
  vision:         { provider: anthropic, model: claude-haiku-4-5 }
  web_extract:    { provider: anthropic, model: claude-haiku-4-5 }
  compression:    { provider: anthropic, model: claude-haiku-4-5 }
  session_search: { provider: voyageai,  model: voyage-3 }
  curator:        { provider: anthropic, model: claude-sonnet-4-6 }

toolsets:
  - hermes-cli
  - hermes-web-search
  - hermes-code-execution
  - research-external               # 신규: arXiv·GitHub·Tavily·Patent
  - knowledge-db                    # 신규: Qdrant CRUD + dedupe

memory:
  memory_enabled: true
  memory_char_limit: 4000           # was: 2200
  user_char_limit: 2000             # was: 1375

cron:
  wrap_response: true
  jobs:
    - name: topic_crawl_daily
      schedule: "0 3 * * *"
      command: "hermes researcher crawl --mode daily"
    - name: topic_crawl_weekly
      schedule: "0 4 * * 0"
      command: "hermes researcher crawl --mode weekly"
    - name: topic_curation_weekly
      schedule: "0 5 * * 6"
      command: "hermes researcher curate-topics"
    - name: cost_report_weekly
      schedule: "0 18 * * 0"
      command: "hermes report cost --period 7d --notify telegram"
```

## 8. 신규 toolset 명세

### 8.1 `research-external`

| Tool | API | 용도 |
|------|-----|------|
| `arxiv_search` | export.arxiv.org/api/query | 논문 검색 (cs.*, physics.*) |
| `semantic_scholar_search` | api.semanticscholar.org | 인용 그래프, 추천 |
| `github_search` | api.github.com/search/repositories | 오픈소스 검색 |
| `tavily_search` | api.tavily.com | 일반 웹·뉴스·블로그 |
| `patent_search` | Google Patents (SerpAPI 또는 직접) | 상용·특허 |
| `archive_wayback` | archive.org/wayback | 사라진 프로젝트 복구 |
| `pdf_extract` | Tika 또는 Unstructured | PDF → text+meta |

### 8.2 `knowledge-db`

| Tool | 동작 |
|------|------|
| `kb_search` | Qdrant cosine search, 컬렉션 필터, top_k |
| `kb_upsert` | dedupe(content_hash) → upsert |
| `kb_topic_register` | topics 컬렉션에 추가 |
| `kb_topic_list` | active 토픽 목록 |
| `kb_stats` | 컬렉션별 점수, dedupe rate, 토큰 절감 |

## 9. 토큰 절감 메커니즘 (정량 측정 가능)

| 메커니즘 | 효과 추정 | 측정 방식 |
|---------|----------|----------|
| RAG로 풀 컨텍스트 대체 | 입력 토큰 30~50% ↓ | sessions DB의 input_tokens 추이 |
| 1h prompt cache | cached input 토큰 90% 할인 | Anthropic 응답의 cache_read_tokens |
| Researcher dedupe | 같은 논문/repo 재인덱싱 0건 | content_hash 충돌 카운트 |
| Continuous indexing | 사용자 질문 시 외부 호출 빈도 ↓ | researcher.search_external 호출 / 질의 비율 |
| Delegation 라우팅 | 가벼운 작업은 Haiku/DeepSeek | provider별 토큰 분포 |

→ 매주 cost report에 모두 반영.

## 10. 비용 추정

가정: 일 ~30만 입력 / ~15만 출력 + cron 작업 일 ~10만 토큰.

### Phase 1 (클라우드 풀스택)

| 항목 | 단가 | 월 비용 |
|------|------|--------|
| Opus 4.7 input (cache 70%) | $0.30/M cached, $3/M | ~$45 |
| Opus 4.7 output | $15/M | ~$67 |
| Sonnet 4.6 (code/researcher) | $3 in / $15 out | ~$18 |
| Haiku 4.5 (light·delegation) | $0.20 in / $1 out | ~$8 |
| DeepSeek V4 (fallback) | $0.27 in / $1.10 out | ~$5 |
| Voyage-3 embedding | $0.10/M | ~$3 |
| Tavily search | $0.005/query | ~$5 |
| Qdrant Cloud free → $25 | — | $0~$25 |
| **합계** | | **~$150~180 (약 20~24만원)** |

→ 사용자 답변 범위(15~30만원) 안.

### Phase 2 (하이브리드)

Light·code·researcher 분이 로컬로 빠지면서:

| 항목 | 월 비용 |
|------|--------|
| Opus 4.7 (orchestrator only) | ~$80 |
| 외부 API (Tavily, SerpAPI) | ~$10 |
| 전기료 (AI 머신, 24시간 idle + 8시간 추론) | ~$15 |
| **합계** | **~$105 (약 14만원)** + AI 머신 감가상각 |

## 11. 도입 단계

### Phase 1 — 즉시 시작 (예상 2~3일)

1. 환경 변수 등록: `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `VOYAGE_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `TAVILY_API_KEY`, `GITHUB_TOKEN`
2. config.yaml 변경 사항 적용 + `restore.sh`로 원복 가능 확인
3. Qdrant Cloud 가입 → 10개 컬렉션 생성 (§5.2 스키마)
4. 신규 toolset 2개 (`research-external`, `knowledge-db`) 구현 — Python/TS 모두 가능
5. 초기 데이터 인덱싱 (1회):
   - `mythrill-pipeline` 코드 → `game_code`
   - Obsidian Vault → `personal_notes`·`game_lore` (자동 분류)
   - 신화 자료 PDF/텍스트 → `game_lore`
6. Topic 추천 → 사용자 승인 → `topics` 컬렉션 등록
7. Cron 4개 작업 등록·동작 확인
8. 평가:
   - chat UI(claude.ai)와 동일 prompt 5개로 답변 비교 (정성)
   - 1주일 사용 후 토큰 통계 vs 도입 전 비교

### Phase 2 — AI 머신 도착 후 (예상 2~3일)

1. AI 머신 셋업: vLLM 또는 LM Studio + Hermes 4 70B + Qwen3-Coder + BGE-M3
2. Qdrant 도커 셀프호스트, Phase 1 snapshot 복원
3. Tailscale로 M1 Air ↔ AI 머신 사설망
4. config.yaml `delegation.routes`·`auxiliary` 모델을 로컬 OpenAI 호환 엔드포인트로 변경
5. 클라우드 fallback 유지 (로컬 다운 대비)
6. 1주일 평가: latency, 비용, 품질, dedupe rate

## 12. 위험·미결 사항

| 항목 | 위험 | 완화 |
|------|------|------|
| AI 머신 미정 | Mac Studio M5 vs DGX Spark 결정 안 됨 | Phase 1은 무관. 출시 후 벤치 비교 |
| Hermes 4 통합 | Hermes Agent와 자체 모델 통합 미검증 | Phase 1 종료 시 사전 테스트 spike |
| Noise 토픽 누적 | 자동 추천이 잡음 토픽을 등록 | weekly curation cron이 archive 후보 제시 |
| 외부 API 한도 | Tavily·SerpAPI 무료 한도 초과 | 일/주 호출 한도 카운터, 초과 시 로컬 큐로 |
| 라이선스·저작권 | 논문·상용 자료 인덱싱 시 내부 사용 한정 | 모든 청크에 `license` 필드, 공개 답변 시 인용만 |
| 토큰 폭증 | heavy 사용 시 30만원 초과 가능 | 월 한도 알람, 가벼운 작업 delegation 강제 |
| Voyage API 종속 | 회사 정책 변경 시 임베딩 재계산 필요 | Phase 2 BGE-M3 이주로 대비 |
| Qdrant 셀프호스트 운영 | AI 머신 다운 시 RAG 죽음 | Cloud fallback 동기 또는 daily snapshot |

## 13. 성공 기준

- chat UI(claude.ai) 대비 동일 prompt 답변 품질 80% 이상 (정성 평가)
- Phase 1 도입 후 1개월 입력 토큰 30% 이상 감소
- `topics` 컬렉션에 10개 이상 active 토픽 등록·매일 인덱싱
- 답변 90% 이상에 출처 인용 자동 포함
- Phase 1 월 비용 30만원 이내
- Phase 2 전환 후 latency 동등 이상, 비용 50% 이상 절감
- Researcher가 매주 새 자료 평균 50건 이상 누적 (소스 다양성: 4종 이상)

## 14. 다음 단계

본 spec 사용자 승인 후 `superpowers:writing-plans` 스킬을 호출하여 **Phase 1 단계별 구현 plan**을 작성한다. Phase 2 plan은 AI 머신 결정·도착 시점에 별도 spec으로 분리한다.

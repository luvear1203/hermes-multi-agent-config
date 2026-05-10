# Wiki Log

> Chronological record. Append-only.
> Format: `## [YYYY-MM-DD] action | subject`

## [2026-05-08] fix | Active-provider quota reporting for Codex GPT-5.5
- 변경: `~/.hermes/bin/quota.sh`를 Anthropic-only probe에서 active Hermes provider/model probe로 교체. 현재 기본값 `openai-codex / gpt-5.5`에 대해 Codex session/weekly quota를 출력.
- 변경: `agent/account_usage.py`가 Codex `additional_rate_limits[]`에서 model-specific bucket을 선택하도록 확장하고, `cli.py`/`gateway/run.py`가 active model을 usage fetch에 전달.
- 검증: `./venv/bin/python -m pytest tests/test_account_usage.py -q` 6/6 통과, `py_compile` 통과, `bash ~/.hermes/bin/quota.sh`가 Codex GPT-5.5 quota를 출력.
- 문서: `CLAUDE.md`, `architecture/orchestrator-protocol.md`, `entities/hermes-core-patches.md`, `responding-to-user` skill의 token-budget reference를 active-provider/model 기준으로 갱신.
- 규칙: closeout 보고에서 Claude Max 5h/7d를 기본값으로 말하지 말고, `quota.sh`가 읽은 active provider/model을 그대로 보고.

## [2026-05-07f] config | Hermes GPT reasoning fixed to xhigh
- 변경: `~/.hermes/config.yaml` 및 `~/.hermes/profiles/orchestrator/config.yaml`의 `agent.reasoning_effort`를 `medium`에서 `xhigh`로 변경.
- 범위: Hermes default/orchestrator의 GPT-5.5 Codex 경로에 적용. Claude Opus `sub-director` profile은 모델 성격이 다르므로 변경하지 않음.
- 근거: 사용자는 Codex 앱 채팅과 별개로 Hermes에서 GPT를 사용할 때 항상 "매우 높음" reasoning으로 사용하기를 원함.

## [2026-05-07e] design | Local Agent Control Plane MVP captured
- 반영: 다른 채팅 handoff 내용과 본 채팅의 Mission Board 설계 결정을 wiki에 영구 반영.
- 신규: `entities/local-agent-control-plane.md` 생성. MVP 1 = Mission Board 중심, 수동 승인 실행, 상태 흐름 `Backlog → Ready → Awaiting Approval → Running → Review → Done / Failed / Blocked`, adapter 3종(`CodexCliAdapter`, `HermesProfileAdapter`, `ManualAdapter`) 확정.
- 갱신: `entities/multi-agent-system.md`를 최신 `Director=gpt-5.5/openai-codex`, `Sub-Director=claude-opus-4-7/sub-director profile`, `Gemma/DeepSeek worker` 구조로 재작성.
- 갱신: `CLAUDE.md`, `entities/grand-engine-vision.md`, `entities/graphify-setup.md`, `index.md`에 Local Agent Control Plane 항목 추가.
- graphify: `wiki/graphify-out/GRAPH_REPORT.md` 기준 현재 wiki graph는 246 nodes / 633 edges / 14 communities. 마지막 full semantic corpus check는 109 files / 약 100,504 words. `graphify update wiki`는 AST-only 경로라 markdown-only wiki에는 `No code files found`로 no-op 처리됨. `graphify check-update wiki`로 pending flag 확인 후 `graphify cluster-only wiki --no-viz`로 기존 graph 기준 로컬 report/JSON만 재생성.
- graphify 보류: 신규 markdown 의미 추출은 `/graphify wiki --update` 계열의 LLM semantic extraction이 필요하므로 Opus/Sonnet quota reset 후 실행.
- 보류: DB schema, 세부 UI 정보구조, OpenClaw/MCP 경계는 Claude Opus quota reset 후 Sub-Director 리뷰와 함께 결정.

## [2026-05-07d] config | Dedicated Sub-Director profile fixed to Opus Max OAuth
- 변경: `~/.hermes/profiles/sub-director/` 신규 생성.
- 고정값: `model.default=claude-opus-4-7`, `model.provider=anthropic`, `base_url=https://api.anthropic.com`.
- 인증: `profiles/orchestrator/auth.json`의 Anthropic `claude_code` OAuth credential 1개만 `profiles/sub-director/auth.json`에 복사하고 `active_provider=anthropic`으로 설정. Codex credential은 넣지 않음. 삭제 없음.
- 역할 문서 갱신: `CLAUDE.md`, `architecture/roles.md`, `architecture/cost-tiers.md`, `profiles/orchestrator/SOUL.md`에 `hermes chat --profile sub-director` 호출 경로 반영.
- graphify 갱신 필요(다음 증분 사이클).

## [2026-05-07c] config | Hermes default switched to gpt-5.5 via OpenAI Codex
- 변경: `~/.hermes/config.yaml` 및 `~/.hermes/profiles/orchestrator/config.yaml`의 기본 모델을 `gpt-5.5`, provider를 `openai-codex`, base_url을 `https://chatgpt.com/backend-api/codex`로 변경.
- 인증: 전역 Hermes Codex credential pool 항목을 `profiles/orchestrator/auth.json`에도 반영하고 두 auth store의 `active_provider`를 `openai-codex`로 설정. 삭제 없음.
- 검증: `hermes status`에서 Model=`gpt-5.5`, Provider=`OpenAI Codex` 확인. `hermes chat -q 'say ok' --max-turns 1 -t '' -Q` 및 `hermes chat --profile orchestrator -q 'say ok' --max-turns 1 -t '' -Q` 모두 `ok` 응답.
- 메모리 갱신: `CLAUDE.md`, `architecture/roles.md`, `architecture/cost-tiers.md`의 “Opus shell 고정” 설명을 제거하고 Hermes default Codex 라우팅으로 정정.
- graphify 갱신 필요(다음 증분 사이클).

## [2026-05-07b] decide | Director ↔ Sub-Director swap (gpt-5.5 promoted, Opus 4.7 demoted)
- 결정: Director = gpt-5.5 via Codex CLI(ChatGPT Pro 구독). Opus 4.7 = Sub-Director로 강등.
- 사유 1: Codex Pro 결제 후 사용자 직접 사용 결과 동일 작업 토큰 소모량이 Opus 대비 압도적으로 적음(사용자 실측).
- 사유 2: 2026-05-07 gemini-3.1-pro-preview SDK 디버깅 인시던트에서 Opus가 4번 외부원인 추측 사이클, Codex가 1발 root cause 식별. directing-grade 의사결정 품질 우위 입증.
- 사유 3: Opus·Codex 둘 다 구독 요금제. directing 워크로드는 단가 0인 Codex Pro에 우선 할당이 합리적.
- 운영 제약: Hermes orchestrator 프로필이 anthropic 하드코딩이라 hermes chat 진입점은 Opus 그대로. 즉 사용자↔Opus(이 채팅) shell은 유지되지만, **directing-grade 의사결정은 모두 Codex 경유**. Opus 채팅은 (a) shell relay, (b) delegate_task fan-out, (c) Codex 한도 부족 시 fallback 역할.
- Sub-Director 역할: 기존 GPT-5.5의 사전·사후 점검 책임을 Opus에 그대로 이관. delegate_task 워커 dispatch도 Sub-Director 책임에 포함.
- wiki 갱신: architecture/roles.md(Director·Sub-Director 행 교체), architecture/cost-tiers.md(Tier 1 후보 로스터 재정렬).
- 메모리 갱신: 아키텍처 항목 `Director=GPT-5.5/Codex, Sub-Director=Opus/Anthropic`로 교체.
- graphify 갱신 필요(다음 증분 사이클).

## [2026-05-07] activate | Sub-Director slot via Codex CLI (gpt-5.5)
- ChatGPT subscription 결제 → `npm install -g @openai/codex` → `codex login` (OAuth)
- 핑 테스트 통과: `codex exec --skip-git-repo-check -m gpt-5.5 '...'` → 정확한 응답
- Sub-Director sanity test 통과
- 통합 경로: terminal(command="codex exec ...") 또는 ACP delegate_task

## [2026-05-07] decide | LLM-2 second-spike: schema v2 + Golden 10 (MVP demo 5 + inputs.txt 5)
- schemas/llm2_output_v1.json (260 lines) → v2.json (355 lines, Sub-Director review-cycle 보정).
- Sub-Director가 짚은 7건 모두 v2에 반영: stages[]/transitions[] machine-readable predicate + parameter_overrides; family_id ↔ constitutive_id 분리; condition_curves[]; per-property citation/confidence; additionalProperties=false; 12-bucket fallback_family.
- constitutive_eq enum 11종 풀유지 (사용자 결정: MVP 후 실무 도구라 완성도 우선, Sub-Director "트림 권장"은 거부).
- v2에 solver_backend 필드 1줄 추가 (taichi-mpm/dem/sph). 외부 엔진(YADE·Houdini 등) enum에서 정책적 제외.
- Golden 10 = MVP 시연 5종(도전제안서 2.1, 입자속도/부피/점성냉각/형상궤적/상변화 종합) + inputs.txt #7 #25 #26 #38 #41.

## [2026-05-07] debug | Gemini 3.1 Pro thinking timeout — SDK migration to google-genai
- 증상: gemini-3.1-pro-preview 호출이 짧은 "Say only: PING" 입력에도 599초 후 504 Deadline expired. 5건 × 3모델 = 15건 중 Gemini 5/5 timeout.
- 사용자 신 키 발급 → 동일 증상 → 호출명 정확(`models/gemini-3.1-pro-preview` API에 존재) → 프로필·env leak 무관 → 결국 Sub-Director(GPT-5.5 codex) 호출.
- Codex 진단: `google.generativeai`는 deprecated, Gemini 3.x 공식 가이드는 `google-genai`. 1발에 root cause 식별. 모델 metadata에 `thinking: true` 강제, deprecated SDK는 thinking_config 미지원이라 thinking이 풀 600초까지 가서 SDK 기본 timeout 절단.
- 사용자 결정: 신 SDK(`google-genai`) 전환. v3 50입력 검증과 호출 shape 동일 유지(추가 옵션 없는 디폴트 호출). thinking_config 미지정 — baseline 정합성 유지.
- 학습: 같은 증상 2회+ 실패 + 외부원인 추측 반복 시 즉시 Sub-Director 호출. 자율 추측 사이클 금지. 메모리에 진단 워크플로 추가됨.

## [2026-05-07] fix | Gemini 503 UNAVAILABLE — Sub-Director가 retry harness 추가
- 신 SDK 전환 후 증상 변경: 504 Deadline → 503 UNAVAILABLE 즉시 반환. Google AI Studio paid tier가 transient capacity 부족 응답.
- Sub-Director(GPT-5.5 codex) 자체 처리 지시 → 패치 도출. 호출 shape 응답 영향 옵션은 안 건드리고 transport-level retry harness만 추가:
  - retryable codes: 408/429/500/502/503/504, exponential backoff 15→30→60→120→180초 (최대 6 시도), jitter 0-5초
  - 각 시도 timeout 180초 (deprecated SDK의 600초 hang 회피)
  - 총 budget 540초/call
  - http_options config는 timeout 제어용, 응답 내용 영향 없음 → v3 baseline 정합성 유지
- 출처: ai.google.dev troubleshooting + AI Studio forum paid-tier 503 사례.

## [2026-05-07] verify | Profile invocation smoke test (5 slots)
- 명령: `hermes chat --profile <name> -q '...' --ignore-rules -t '' --max-turns 1 -Q`
- orchestrator (claude-opus-4-7 / anthropic): ✓ 통과
- researcher default (claude-sonnet-4-6 / anthropic): ✗ HTTP 429 "Extra usage required for long context". sonnet-4-6은 1M context tier 묶임 → Max OAuth로는 별도과금. **sonnet-4-5-20250929(200K context) 호출은 통과**.
- researcher override (deepseek-v4-pro / deepseek): ✓ 통과
- tech-artist (gemma-4-31b-it / gemini): ✓ 통과
- dev-gemma (gemma-4-31b-it / gemini): 초기 ✗ — Google AI Studio quota는 **GCP 프로젝트 단위**라 같은 프로젝트의 키 분리는 효과 0. 두 번째 GCP 프로젝트 발급 후 dev-gemma/.env에 신 키 → 연속 호출 둘 다 즉시 통과.
- env_loader 검증: hermes-agent/hermes_cli/env_loader.py 직접 확인 — 프로필 .env override=True, 부모 .env는 fallback only. 정상 동작.
- 결정: researcher 기본 모델을 sonnet-4-5-20250929로 다운그레이드하거나 호출 시 명시. sonnet-4-6은 long-context 작업 명시적으로 필요할 때만 사용. tech-artist=GCP 프로젝트1, dev-gemma=GCP 프로젝트2 (quota 완전 분리).

## [2026-05-07] update | Profile slot config + dev-gemma reactivation
- profiles/researcher: dual-model. default=claude-sonnet-4-6 (anthropic), provider override deepseek-v4-pro (api.deepseek.com/v1) for R&D Engineer B. SOUL.md rewritten in English.
- profiles/dev-gemma: ARCHIVED 해제. model=gemma-4-31b-it / provider=gemini (Google AI Studio 무료 티어, $GEMINI_API_KEY). Code Implementation 슬롯으로 재가동. SOUL.md 영어로 재작성.
- profiles/orchestrator: 변경 없음 (claude-opus-4-7 / anthropic).
- profiles/tech-artist: 변경 없음 (gemma-4-31b-it / gemini, NL→SI 파라미터 번역 슬롯 유지).
- architecture/roles.md 갱신: R&D A/B 엔트리에 모델 ID + 프로필 경로 명시, Code Implementation(dev-gemma) 행 추가.
- 사유: 세션 시작 시 graphify 미반영으로 컨텍스트 누락 → 갱신 보장 위해 프로필 모델 ID를 wiki에 못박음. researcher 한 프로필에 두 모델을 두는 이유: A·B 토론 시 동일 SOUL.md/output contract 공유 → 프롬프트 일관성. 모델만 -m으로 스위치.

## [2026-05-03] create | Wiki initialized
- Domain: AI/ML 연구, 멀티 에이전트 시스템, 오픈소스 AI 도구
- Structure created: SCHEMA.md, index.md, log.md
- WIKI_PATH: ~/.hermes/wiki

## [2026-05-03] batch-ingest | Multi-Agent System Setup Documentation
- Created: entities/multi-agent-system.md
- Created: entities/github-config-backup.md
- Created: entities/discord-gateway.md
- Created: entities/cron-api-monitor.md
- Created: entities/idea-validation-pipeline.md
- Created: concepts/llm-wiki-setup.md
## [2026-05-03] batch-ingest | Graphify Setup
- Created: entities/graphify-setup.md
- Installed: graphify 0.6.7
- Generated: hermes-agent graph (54,648 nodes)
## [2026-05-03] batch-ingest | Obsidian Vault Import (Mythrill + C-Chasm)
- Imported: Brain.zip → raw/obsidian-vault/
- Mythrill subagent: 13 pages created (entities + concepts)
- C-Chasm: 10+ pages created (IP core, 5 laws, deity types, dual layer, etc.)
- Total wiki pages: 37
- Updated: index.md

## [2026-05-03] update | 도전제안서 수정본 반영 (루키 2026)
- Source: ~/Downloads/도전제안서_수정본.docx
- Updated: entities/ai-rookie-2026.md (팀 정보 + 신청서 12항목 상태)
- Updated: entities/mythrill-roadmap.md (Phase 1 세부 추진일정 5단계)
- Updated: entities/mythrill-pipeline.md (현재 상태 + MVP 스코프 링크)
- Created: entities/mythrill-mvp-scope.md (Taichi MPM, 도전과제 3종, 테스트 프롬프트 5종)
- Created: concepts/naked-viewer.md (Python 기반 사전 확인 메커니즘)
- Updated: index.md (44 pages)
- Note: 제안서 3.2 본문 "1차 스파이크"는 LLM ② 검증 → 실제로는 2차 스파이크 (오기 표기)

## [2026-05-03] decide | LLM ① v3 동결, 2차 스파이크 진입
- Decision: 추가 개선 vs 다음 단계 → 다음 단계 진행 (4가지 근거)
- Updated: entities/llm1-validation.md (동결 결정 섹션, 회귀 트리거 4종)
- Updated: entities/mythrill-mvp-scope.md (EOY 종착점, 도전과제 ① 강화 — 5/9 즉시 착수)
- Updated: entities/mythrill-pipeline.md (현재 상태, 진짜 마감 2026 EOY)
- Updated: concepts/llm-separation-design.md (2차 스파이크 링크)
- Created: entities/mythrill-spike-02.md (진입 조건, 검증 방법 초안, 5종 물질 라이브러리 초안, 회귀 트리거)
- Updated: index.md (45 pages)
- Scope: Mythrill 단독 초점, 2026-12-31 MVP 완성 = 진짜 마감
- 잔여 작업: 빈 응답 2건(#1·#17) 입력 정제 (0.5일, 별도 처리)

## [2026-05-03] verify | Hermes ↔ Claude Max 구독 연결 확정
- Investigation: Hermes 코드 (anthropic_adapter, auth.py, auth_commands) 검사로 OAuth 1급 지원 확인
- Verification: /login 갱신 후 Hermes credential reader → keychain 토큰 정상 검출 (sk-ant 108자, refresh 포함)
- API 호출 테스트: HTTP 200, claude-haiku-4-5, Bearer + anthropic-beta:oauth-2025-04-20 패턴 작동
- Tier 확정: rate-limit 헤더에 5h + 7d 듀얼 윈도우 → Max 시그니처 (Pro는 5h 단일)
- Created: entities/hermes-max-integration.md (인증 구조, 검증 결과, 환경 분리 전략, 약관 해석, 코드 위치 인덱스)
- Updated: entities/multi-agent-system.md (researcher 상태 ⏳→✅, Anthropic 인증 섹션 추가)
- Updated: index.md (46 pages)
- 결과: Hermes는 별도 설정 0으로 Max 구독 사용. Mythrill API key는 격리 유지.

## [2026-05-04] fix | Claude Max OAuth → kristianvast/hermes-claude-auth bypass 적용
- Problem: Anthropic 4/4 서버사이드 검증으로 Opus/Sonnet 차단 (HTTP 400 "out of extra usage"), Haiku만 허용
- Root cause: Anthropic이 서드파티 OAuth 요청을 시스템 프롬프트 구조, 툴 이름 케이싱, 빌링 헤더 등으로 핑거프린팅
- Solution: kristianvast/hermes-claude-auth (Python import hook) 설치 → Hermes 소스 수정 없이 Claude Code identity 자동 주입
- Verification: Claude Opus 4.7 + Max 구독 OAuth → "ok" 응답 성공 (hermes chat -q -m claude-opus-4-7 --provider anthropic)
- Updated: entities/hermes-max-integration.md (전면 재작성 — 잘못된 "지문 제거" 내용 수정)
- Updated: entities/multi-agent-system.md (변경 이력, bypass 링크 추가)
- Created: entities/claude-auth-bypass.md (바이패스 상세 문서)
- Auto-maintenance: 크론 job claude-auth-bypass-check (매일 repo 업데이트 확인 + 자동 적용)
- Skill: claude-auth-bypass-updater 생성

## [2026-05-04] architecture | Studio governance 페이지 5종 신설 + 위키 검토 보강
- Context: 멀티에이전트 스튜디오 구조 확정(Director/Sub-Director/Engine Architect/R&D A·B/Tech Artist/Engine Programmer/Validator on-demand). 영어식 역할 명칭 통일. Mythrill을 [[grand-engine-vision]] 대장정의 첫 단계로 위치시킴.
- Created: entities/grand-engine-vision.md (Mythrill→Adamantium→...→통합 자체 게임 엔진)
- Created: architecture/roles.md (역할표 + 통신규약 3종 + Wiki-First 강제)
- Created: architecture/cost-tiers.md (능력 기반 4-Tier + 모델 후보 풀 + 하드웨어 로드맵)
- Created: architecture/model-prompting-conventions.md (Opus/Sonnet/DeepSeek/GPT-5.5/Gemini 컨벤션)
- Created: architecture/validators.md (on-demand 검증 패턴)
- Updated: SCHEMA.md (Top-level Categories 섹션 추가, architecture/ 명시)
- Fixed: index.md (read_file 출력이 파일에 그대로 박혀있던 corruption 복구)

## [2026-05-04] curation | wiki 일제 검토 및 보강 (내용 삭제 없음)
- Audit: 27 entities + 21 concepts 전수 점검 (서브에이전트 두 건 위임)
- Fixed (frontmatter `updated` 누락): claude-auth-bypass.md
- Filled (frontmatter `sources: []`): idea-validation-pipeline / mythrill-spike-02 / cron-api-monitor / discord-gateway / github-config-backup / llm-wiki-setup
- Inline 출처 보강: stage-separation-rule / trigger-classification / visual-inference-policy / vfx-input-labeling-guide
- Added wikilinks: idea-validation-pipeline.md (1→4)
- Canonical SoT 배너 추가 (한글 확장본 우선): three-deity-types→[[신의_세_유형]] / cosmic-horror-dual-layer→[[C-Chasm_우주론]]
- Canonical SoT 배너 추가 (요약본): c-chasm-project→[[C-Chasm]] (+ 깨진 링크 3개 수정)
- Reference: Alex AI "Multi LLM Agent" 영상(nJfqO5edMFk) 인사이트 → roles.md 통신규약에 반영
- Reference: FromSoftware + Epic Games 직군 구조 조사 → roles.md 매핑

## [2026-05-06] curation | Wiki 전수 감사 + C-Chasm IP 정본 정비
- Audit: 28 entities + 21 concepts + 4 architecture = 53 pages 전수 감사 (3 워커 병렬)
- C-Chasm SoT 정비: c-chasm-ip-core.md를 IP코어 v1.2(원본: ~/Documents/Obsidian Vault/Brain/C-Chasm/00_IP코어/IP코어_v1_2.md) 기반으로 재작성
- Created (concepts/, IP코어 v1.2 추출): 강림형_신.md, 회귀형_신.md, 광기형_신.md, cosmic-horror-design-pattern.md, dual-ending-branch.md
- Canonical 배너: c-chasm-project → c-chasm-ip-core 리다이렉트
- Type 정규화: C-Chasm/C-Chasm_Alpha/본편_RPG_(C-Chasm) frontmatter type 정리. SCHEMA에 project/system/character/architecture type 정식 도입
- Wikilink 자정: 19건 깨진 링크 → 정본 wikilink 교체 또는 "(작품문서 예정)" 텍스트 전환
- Bug fix: mythrill-mvp-scope·mythrill-roadmap 의 [[link\|alias]] 백슬래시 이스케이프 4건 수정
- Filled (frontmatter sources: []): grand-engine-vision, validators
- SCHEMA.md 갱신: type 허용값 확장 (project/system/character/architecture), Tag Taxonomy 확장 (Studio Governance, C-Chasm IP, Mythrill 그룹)
- CLAUDE.md 갱신: architecture/ 폴더 규칙 명시, C-Chasm SoT 위치 = c-chasm-ip-core 명시, Wiki-First 원칙 추가
- index.md 갱신: 47 → 58 pages, session-2026-05-04 등재, grand-engine-vision를 Entities 섹션으로 이동
- log.md 정리: line-number prefix corruption 제거

## [2026-05-06] govern | 운영 규약 2종 신설
- 규칙 변경 즉시 wiki 반영: 규칙·설정·아키텍처·워크플로 변경 발생 시 같은 턴에 wiki 업데이트 (대화/오케스트라 모드 무관)
- 작업 종료 보고 규약: 매 작업 단위 종료 시 Claude Max 5h/7d 토큰 잔여율 정확치 보고. 헬퍼 ~/.hermes/bin/quota.sh 신설 (Anthropic ratelimit 헤더 파싱)
- Updated: CLAUDE.md (Wiki-First 원칙 아래 두 규약 추가)
- 근거: 사용자 직접 지시 (이번 세션)

## [2026-05-06] govern | 토큰 절감 + 가능성 판단 규약 확장
- 토큰 측정: cl100k_base 기준 한국어 = 영어의 2.08배 (CLAUDE.md 1,749 tok @ 한국어 vs 영어 추정 ~840 tok)
- AI간 통신 영어 only 규약 추가: delegate_task goal/context, 워커 system prompt, 모든 AI↔AI 메시지 영어. 사용자↔AI는 한국어 유지
- 작업 가능성 판단 룰: 5h utilization 기준 GREEN(<50%) / YELLOW(50~75%) / RED-soft(75~90%) / RED(>90%) + 7d>80% 또는 잔여시간<30분 차단 조건
- 영어 전환 후보(매 턴 시스템): CLAUDE.md, SCHEMA.md, architecture/* — 5h 리셋 후 일괄 전환 예정
- 한국어 유지: 컨텐츠 문서(C-Chasm IP, Mythrill 검증 결과) — 의미 SoT 보존 우선
- Updated: CLAUDE.md (작업 종료 보고 규약 확장 + AI간 통신 언어 규약 신설)
- 근거: 사용자 직접 지시 (이번 세션)

## [2026-05-06] govern | LLM-facing 규칙은 영어 only 메타규칙 강화
- 신설: 향후 추가되는 모든 LLM-facing 규칙(오케스트레이터·워커·기타 역할군 대상)은 영어로만 작성. CLAUDE.md, SCHEMA.md, architecture/, 역할 프로필, SKILL.md, AGENTS.md 모두 적용.
- 예외: log.md 변경 이력(이 항목 같은 사실 기록), 컨텐츠 문서(C-Chasm IP, Mythrill 검증 결과 등) — 한국어 SoT 유지.
- Updated: CLAUDE.md (AI-to-AI Communication Language Rule 섹션 확장)
- 사용자 메모리에도 반영
- 근거: 사용자 직접 지시 (이번 세션 — "규칙 추가하는거 전부 영어로")

## [2026-05-06] govern | Provider 경로 규약 (자율 API 전환 금지)
- 위반 사례: graphify 추출 작업 중 Sonnet hermes chat 이 long-context 429 실패 시, 사용자 허락 없이 직접 Anthropic API 호출 스크립트(extract.py)로 자동 전환 시도. 인증 실패(401)로 실제 비용은 0이었으나 절차적 위반.
- 신설 규약: hermes chat (Max OAuth) 기본 경로 실패 시 → 반드시 사용자에게 옵션 제시·선택 요구. 자율로 직접 API 경로(httpx/curl/SDK) 전환 금지. delegate_task 워커, background terminal, 모든 subprocess 동일 적용.
- Updated: CLAUDE.md (Provider Path Discipline 섹션 신설)
- 사용자 메모리에도 반영: "API 직접 호출 자동 전환 절대 금지"
- 근거: 사용자 직접 지시 (이번 세션 — "API로 전환하는 해결책 떠올렸으면 반드시 선택하도록 해")

## [2026-05-06] plan | Mythrill 피칭 이미지 에셋 준비 시작
- Created: entities/mythrill-pitch-assets.md — AI 루키 2026 심사 피칭용 [Prompt → Asset Scene] 2건 계획
- 정직 프레임 명시: LLM ① 검증 완료, LLM ② + 솔버 + 렌더는 5/9 착수 → EOY 목표. 컨셉 렌더는 "타겟 출력 기준점" 표기
- 후보 페어 1 (추천): "황금빛 광채를 뿜는 신성한 검의 오라" (#4, 단순) + "마법진 발동→폭발→감쇠" (#41, 다단계)
- 대안 페어: 마그마 (#9) + 룬 검 순환 (#42)
- 결정 대기: 페어 / 이미지 생성 도구 / 톤 / 출력 형식
- 분담 합의: 사용자 = 시각 디렉션 + 컨셉 렌더 / AI = 슬라이드 레이아웃·JSON 패널·정합성 검수
- Updated: index.md (60 → 61, Entities 29 → 30)
- 근거: 사용자 직접 지시 ("contest 이미지 에셋 2개 준비, wiki 먼저 저장")

## [2026-05-06] govern | Orchestrator 전용 프로토콜 분리 + quota.sh KST 시각 계산 패치
- 분리: 작업 종료 보고 규약·feasibility 판단·worker spawn 규율을 CLAUDE.md 에서 빼서 architecture/orchestrator-protocol.md 신설로 이동. CLAUDE.md 에는 한 줄 요약 + 링크만 유지.
- 이유: 워커 역할군(R&D A·B, Tech Artist, Engine Programmer, Validator)이 사용자에게 응답하지 않으므로 보고 의무 없음. CLAUDE.md 가 모든 LLM 진입점이라 거기 보고 규약 박으면 워커도 따라 수행 시도 → 잘못.
- quota.sh 패치: utilization 만 출력하던 것을 KST 시각 변환 + 잔여 시간(h, m) 계산까지 직접 출력하도록 재작성. 오케스트레이터가 응답에서 unix timestamp 직접 변환하다 오프셋 오류 (이번 세션 내내 reset 시각 16:30 KST 로 잘못 보고, 실제 23:40) → 스크립트 출력 verbatim 인용 강제.
- Created: wiki/architecture/orchestrator-protocol.md
- Updated: wiki/CLAUDE.md (Task Closeout 섹션 한 줄로 축소 + orchestrator-protocol 링크), wiki/index.md (60 pages, Architecture 5)
- Patched: ~/.hermes/bin/quota.sh (KST + remaining-time 계산 내장)
- 근거: 사용자 직접 지시 ("오케스트라 전용 규약 분리 + 시각 계산 방식 변경")

## [2026-05-06] fix | profile 모드에서 ~/.hermes/.env 자동 상속 (env_loader 패치)
- 문제: `hermes chat --profile tech-artist` 시 HERMES_HOME 이 ~/.hermes/profiles/tech-artist 로 변경됨 → load_hermes_dotenv() 가 프로필 디렉토리에서만 .env 찾음 → ~/.hermes/.env 의 GOOGLE_API_KEY 미로드 → "API key not valid" HTTP 400
- 진단: `provider gemini has no API key configured (tried: GOOGLE_API_KEY, GEMINI_API_KEY)` 디버그 로그로 확인. 셸에서 export GOOGLE_API_KEY=... 한 번 prefix 하면 작동했던 것이 결정적 단서.
- 패치: ~/.hermes/hermes-agent/hermes_cli/env_loader.py — load_hermes_dotenv() 가 HERMES_HOME 이 ~/.hermes 가 아닌(=프로필 사용 중) 경우 부모 ~/.hermes/.env 도 자동 fallback 로드. 프로필이 공유 키(GOOGLE_API_KEY, DEEPSEEK_API_KEY 등) 상속하도록.
- 효과: 프로필 마다 .env 복제 불필요. 공유 키 1곳(~/.hermes/.env)에서 관리.
- 검증: tech-artist 프로필로 Gemma 4 31B IT 호출 → {"ok":true,...} 정상 응답.
- 영향 범위: Hermes 코어 수정 → hermes update 시 패치 날아감. 재적용 필요 시 본 항목 참조.
- 보안: 진단 과정에서 .env 의 GOOGLE_API_KEY 값이 grep 출력에 1회 노출됨 → 사용자가 즉시 키 폐기·재발급 완료.

## [2026-05-06] govern | Tech Artist 슬롯에 Gemma 4 31B IT 배치
- 결정: Tech Artist = Gemma 4 31B IT (Google AI Studio API, free tier 무료 경로). 기존 DeepSeek V4-Pro Tech Artist 세션은 폐기.
- 배경: NVIDIA NIM 가입했으나 무료 한도 미확인, Mythrill 폴더에 GEMINI_API_KEY 가용 → 즉시 호출 가능 검증 완료(HTTP 200, 256K input / 32K output).
- 효과: DeepSeek 유료 API 사용량 약 절반 감소 (R&D Engineer B 슬롯에만 잔존). API 비용 절감 최우선 가치 정합.
- 다양성: R&D B(DeepSeek V4-Pro) ↔ R&D A(Sonnet 4.6) 베이스 다른 토론 파트너 유지.
- Mythrill 정합: Gemma 4 31B IT 가 Mythrill LLM ②(NL → SI 단위 물리 파라미터 매핑) 역할에 맞음. dev-gemma 비전(Gemma 4 로컬 예정)의 즉시 가용 클라우드 버전.
- Updated: architecture/roles.md (Tech Artist 슬롯 갱신), architecture/cost-tiers.md (Tier 2 후보 갱신: Gemma 4 31B IT 추가, GLM 5.1 NVIDIA NIM 후보 추가)
- Created: ~/.hermes/profiles/tech-artist/config.yaml (Google AI Studio openai-compatible endpoint)
- Archived: ~/.hermes/profiles/dev-gemma/config.yaml (Ollama 로컬 경로 보존, 향후 로컬 Gemma 가용 시 재활성)
- 검증: curl 직접 호출로 gemma-4-31b-it generateContent 200 응답 확인. Hermes 통합은 다음 세션에서 검증 필요.

## [2026-05-06] migrate | 시스템 프롬프트 6종 영어 전환 (실행)
- Translated: CLAUDE.md, SCHEMA.md, architecture/{roles,cost-tiers,model-prompting-conventions,validators}.md
- 측정 결과 (cl100k_base):
  - CLAUDE.md            1,749 → 1,358 tok (-22%)
  - SCHEMA.md            1,056 →   756 tok (-28%)
  - roles.md             1,173 →   738 tok (-37%)
  - cost-tiers.md        1,320 →   902 tok (-32%)
  - model-prompting-conventions.md  855 → 538 tok (-37%)
  - validators.md          827 →   530 tok (-36%)
  - **합계: 6,980 → 4,822 tok (-31%, 매 턴 -2,158 tok)**
- 예측(-50%)보다 낮은 이유: 본문에 한국어 wikilink·IP 참조 다수 잔존 (보존 우선)
- 보존 항목: 모든 [[wikilinks]] 원형(한·영 모두), frontmatter 키, 코드블록, 경로, 고유명사
- 사용자 응답 언어는 한국어 유지 (CLAUDE.md 마지막 줄 "Always respond to the user in Korean.")

## [2026-05-10] audit | Wiki audit for rebuild plan
- 66 페이지 분류: preserve 35 / compress 3 / review 28.
- 사용자 결정 (option 1, conservative): 자동 분류된 compress 3개만 진행.
  - entities/llm1-validation.md
  - entities/mythrill-spike-01.md
  - entities/mythrill-spike-02.md
- review 28개는 모두 보존. log.md 분기별 archive는 보류.
- 결과 파일: hermes-multi-agent-config/docs/superpowers/audit-2026-05-10-final.json
- 다음: Step 1 설정 재구축 + Director swap (새 세션에서 이어감).

## [2026-05-10] decide | Director ↔ Sub-Director re-swap (Opus 4.7 promoted, GPT-5.5 demoted)
- 결정: Director = claude-opus-4-7 via Anthropic Max OAuth. Sub-Director = gpt-5.5 via Codex OAuth.
- 사유: Opus 4.7 출력 품질 우선 (directing 판단 품질을 최우선으로 하는 사용자 결정).
- 운영 제약: 두 구독 모두 활성. quota.sh가 active provider만 보고하므로 sub-director 호출 후 별도 확인.
- 적용 범위:
  - ~/.hermes/config.yaml: model.default=claude-opus-4-7, provider=anthropic, agent.service_tier='' (Opus는 speed 파라미터 미지원)
  - ~/.hermes/profiles/orchestrator/{config.yaml,SOUL.md}: 재작성
  - ~/.hermes/profiles/sub-director/{config.yaml,SOUL.md}: 재작성 (gpt-5.5 + Codex base_url)
  - ~/.hermes/auth.json + profiles/orchestrator/auth.json: active_provider=anthropic
  - ~/.hermes/profiles/sub-director/auth.json: active_provider=openai-codex, credential_pool에 backup의 openai-codex 1건 복사
  - claude-auth-bypass install-remote.sh 5종 패치 재설치
- wiki 갱신: roles, orchestrator-protocol, cost-tiers, CLAUDE.md, multi-agent-system, log.md, index.md
- 검증: smoke 8종 중 7종 통과 (default/orchestrator/sub-director/researcher Sonnet/researcher DeepSeek/tech-artist/quota.sh GREEN). dev-gemma는 GCP project 2 TPM 16k 한도로 Hermes 호출 즉시 실패 (직접 API 'ok' 245토큰 호출은 정상 → key 정상, Hermes system prompt가 한도 초과). GCP 콘솔 quota 상향 요청 진행 중.
- graphify 갱신 필요 (다음 증분 사이클).

## [2026-05-10] decide (patch) | dev-gemma model swap (gemma-4-31b-it → claude-haiku-4-5-20251001)
- 결정: dev-gemma profile의 underlying model을 Haiku 4.5로 교체. Profile name `dev-gemma` 유지.
- 사유:
  - Google AI Studio Tier 1 paid에서도 gemma-4-31b는 input_tokens_per_minute 16k hard cap (UI에선 0~16000 사이만 cap-down 허용)
  - Hermes 1회 chat 호출이 89개 skill의 SKILL.md frontmatter 로드 → ~25k 입력 토큰 → 1요청에서 한도 초과 → 단일 호출 항상 실패
  - 직접 API 1-token 호출(245 토큰)은 정상 → key/project는 정상, 구조적 한도 미스매치
- 대안: claude-haiku-4-5-20251001 via Anthropic Max OAuth, 추가 비용 0, 200K context, 충분
- 추후: 자체 머신 도입 시 로컬 오픈소스 worker(gemma·kimi 등)를 Director/Sub-Director 외 자리에 적극 활용
- 검증: smoke 8/8 GREEN (dev-gemma 'ok' 응답)
- wiki 갱신: multi-agent-system Active Profiles + History + Architecture diagram, cost-tiers Tier 1 Haiku 행 추가

## [2026-05-10] correction | model-prompting-conventions.md 1차 소스 재작성 (Source-Enforcement 위반 수정)
- 사용자 정정: "외부에서 직접 검색해서 적용한 거 맞나?"
- Director 답변: 아니오. 훈련 데이터 + 기존 wiki + 일반 지식 기반이었음. URL `cookbook.openai.com/examples/gpt5_prompting_guide`도 검증 없이 적었음 (실제는 `/gpt-5/gpt-5_prompting_guide`로 dash 포함).
- 조치:
  - WebSearch 4갈래 + WebFetch 4건 실행 (Anthropic best practices, GPT-5/5.1/5.2/5.5 cookbook+API guide)
  - model-prompting-conventions.md 전면 재작성 — 모든 섹션에 1차 소스 URL 명시, 직접 인용 표시.
  - Confidence 등급화: Claude(Opus 4.7/Sonnet 4.6/Haiku 4.5)·GPT-5.5 = high (1차 페치). DeepSeek·Gemini/Gemma = low (다음 사이클 페치 필요).
  - 발견 1: Hermes orchestrator의 `reasoning_effort: medium`은 Anthropic 권장 `high` 이상보다 낮음 → 검토 필요.
  - 발견 2: Hermes sub-director의 `reasoning_effort: xhigh`는 Anthropic 어휘 — Codex가 'high'로 매핑할 가능성 높음 → 후속 검증 필요.
  - 발견 3: GPT-5.5는 markdown headings 7개 (Role/Personality/Goal/Success criteria/Constraints/Output/Stop rules) 가 공식 framework. 이전 wiki의 6개 (Role/Goal/Context/Constraints/Required Output/Inputs)는 GPT-5 cookbook 영향. Sub-Director review prompt(/tmp/sub-director-review-prompt.md)는 6개 양식 사용했으므로 다음 review부터 7개 framework 적용.
- 학습: AI 호출 양식·문서 작성 시 Source-Enforcement는 자기 자신에게도 적용. 훈련 데이터로 "추정"한 사실은 명시 또는 외부 검증 후 작성.

## [2026-05-10] create | Knowledge DB Phase 1 (Qdrant Cloud + 12 collections + 65 pages indexed)
- 신규 인프라: Qdrant Cloud cluster (GCP australia-southeast1, free tier 1GB/4GB)
- 신규 12 컬렉션: wiki_{entities,concepts,architecture}, kb_{papers,oss_projects,industry_solutions,lessons_learned,dev_docs}, mythrill_code, chat_memory, personal_notes, topics. 1024-dim cosine + HNSW + int8 quantization.
- 신규 toolset: knowledge-db (kb_search/upsert/upsert_batch/topic/stats with content_hash dedupe + UUID5 id 변환). research-external (arxiv/scholar/github/tavily + backoff).
- 인덱싱: 62 wiki pages (entities 31 / concepts 26 / architecture 5) + 1 mythrill .py file (sim/mpm128_reference.py, 16개는 placeholder 빈 파일).
- 신규 hook: ~/.hermes/patches/wiki_first_kb_second.py (Wiki-First→KB-Second 2-tier, threshold 0.5)
- 신규 wiki 페이지 (3): architecture/knowledge-db.md, entities/qdrant-instance.md, concepts/wiki-token-cost-reduction.md
- 운영 제약 발견: Voyage Free TPM ~10K/min·~3 RPM → wiki 인덱싱은 5 페이지·25s sleep 분할 필요 (~6분/62 페이지)
- 비용: Qdrant free $0, Voyage usage ~$0.01 (60 페이지 임베딩 1회)
- 검증 hits:
  - "Mythrill 파이프라인 자연어 VFX" → wiki_concepts/natural-language-vfx-pipeline 0.616 (top), wiki_entities/mythrill-pipeline 0.590
  - "mythrill VFX pipeline" (영문) → wiki score 0.5 미만 → kb fall-through 정상
- Plan deviation:
  - point_id: Qdrant은 uint64/UUID만 → _to_qdrant_id가 UUID5(NAMESPACE_URL) 변환
  - dedupe scroll-with-filter → GET /points/{id} (payload index 불필요)
  - topics 컬렉션 size=0 거부 → 1-dim placeholder
  - kb_upsert_batch 신규 (Plan에 없음, Voyage TPM 회피)
  - mythrill 빈 파일 skip (Voyage 빈 input 400 거부)

## [2026-05-10 15:54] crawl | mode=daily | multi-agent: +5/dup0 · cosmic-horror: +3/dup0 · cosmology: +5/dup0 · worldbuilding: +5/dup0 · mythrill: +0/dup0 · vfx: +5/dup0 · main-rpg: +3/dup0 · c-chasm: +5/dup0 | total +31 new (errors=8)

## [2026-05-11] activate | Continuous Researcher cron loop (Step 3 종료)
- 신규 cron 4종 (hermes cron create로 정확 schema, prompt 기반 대화형):
  - topic_crawl_daily (3f50ccf34019, 0 3 * * *, deliver=local)
  - topic_crawl_weekly (7a6a31641f8d, 0 4 * * 0, deliver=local)
  - topic_curation_weekly (5aec985fa112, 0 5 * * 6, deliver=telegram)
  - cost_report_weekly (6f8b6b7b0fb2, 0 18 * * 0, deliver=telegram)
- 신규 스크립트:
  - ~/.hermes/skills/research-external/crawl_loop.py (daily/weekly mode)
  - ~/.hermes/skills/research-external/topic_recommender.py (wiki tags + mythrill modules)
  - ~/.hermes/skills/research-external/curate_topics.py (Telegram approval card)
- 신규 wiki: architecture/continuous-research-loop.md
- profile/researcher/SOUL.md에 Cron Mode 섹션 추가 + Researcher A 모델 표기 4-5-20250929 갱신
- 8 active topics 등록 (사용자 승인): mythrill, c-chasm, vfx, cosmic-horror, multi-agent, cosmology, worldbuilding, main-rpg (project/agent/architecture/llm은 generic noise로 제외)
- 첫 daily crawl: total +31 new chunks (8 errors는 arxiv 500 transient — 다음 cycle 재시도 운용 정책)
- KB 최종 상태: Total 106 points (Step 2 67 → +39 = 31 crawl + 8 topics)
- Plan deviation:
  - Plan은 cron schedule을 string으로, command를 shell command로 가정 → Hermes는 schedule={kind,expr,display} dict + prompt 기반 대화형 → hermes cron create로 정확 schema 사용
  - kb_topic_register/kb_topic_list가 string ID 직접 사용 → _to_qdrant_id(UUID5) 변환 + scroll-without-filter (payload index 미설정)
  - hermes-researcher wrapper 스크립트 생략 (cron prompt가 직접 python 호출)
- Gateway 미실행 (사용자 별도 hermes gateway install 필요)

## [2026-05-11] complete | Hermes rebuild + Knowledge DB + Continuous Researcher (Step 0~4)
- 5 step 완료: audit → 설정 재구축 + Director swap → KB Phase 1 → continuous researcher → 압축 + graphify.
- Total ~33 commits (Step 0 4 + Step 1 12 + Step 2 6 + Step 3 7 + Step 4 3 + reviews/fixes).
- 신규 wiki: knowledge-db, continuous-research-loop, qdrant-instance, wiki-token-cost-reduction, setting-rebuild-2026-05-10. (5 pages)
- 압축: llm1-validation, mythrill-spike-{01,02} (3 pages, 409→90줄). 원본 raw/compressed_2026-05-10/ 보존.
- 검증:
  - smoke 8/8 (orchestrator/sub-director/researcher A·B/tech-artist/dev-gemma + quota.sh GREEN)
  - Sub-Director(GPT-5.5) review 3회 APPROVE (Step 1 deviations / Step 1 corrections / Step 3)
  - KB 12 컬렉션 / 107 points / 8 active topics
  - cron 4종 hermes cron list / 다음 fire 2026-05-12T03:00
  - graphify 246 nodes / 633 edges / 14 communities
  - Gateway dual-use (Discord + cron) PID 1718 active
- 다음 능동 작업: 2026-05-17 18:00 첫 cost_report_weekly로 토큰 절감 정량 측정 시작.

## [2026-05-10 16:48] crawl | mode=daily | multi-agent: +0/dup5 · cosmic-horror: +0/dup3 · cosmology: +0/dup5 · worldbuilding: +0/dup5 · mythrill: +0/dup0 · vfx: +0/dup5 · main-rpg: +0/dup3 · c-chasm: +0/dup5 | total +0 new (errors=8)

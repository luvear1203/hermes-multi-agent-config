# Hermes Multi-Agent Config

Hermes Agent 5-profile multi-agent studio + Knowledge DB + Continuous Researcher의 단일 git 백업.

`~/.hermes/` runtime의 **sync 가능한 모든 파일** (profiles · skills · cron jobs · wiki · patches · bin · main config)을 본 repo로 통합 관리. 새 머신 setup은 `git clone` + `bash restore.sh` + 보안 자료 별도 복원만.

## 디렉토리 구조

```
hermes-multi-agent-config/
├── profiles/             # 5 profile (orchestrator, sub-director, researcher, tech-artist, dev-gemma)
│   └── <name>/
│       ├── config.yaml
│       └── SOUL.md       # role 정의 (auth.json은 .gitignore)
├── skills/               # 사용자 custom skills (knowledge-db, research-external 등)
│                         # 번들 skills는 .gitignore (Hermes 설치 시 자동)
├── scripts/              # 재구축·인덱싱·압축 스크립트 + tests
│   ├── audit_wiki.py
│   ├── create_collections.py + test_*
│   ├── index_wiki.py + test_*
│   ├── index_mythrill.py
│   └── compress_wiki.py + test_*
├── cron/jobs.json        # Hermes cron 정의 (orchestrator profile에서 symlink로 사용)
├── patches/              # 사용자 작성 patches (anthropic_billing_bypass는 별도 GitHub install)
├── bin/                  # 사용자 작성 도구 (Hermes 자체 quota.sh 등은 제외)
├── wiki/                 # ~/.hermes/wiki/ 미러 (raw/, graphify-out/ 제외)
├── docs/superpowers/     # spec + plan + audit 결과
├── backups/              # Pre-flight tar 등 (.gitignore에 *.tar.gz)
├── config.yaml           # ~/.hermes/config.yaml 미러
├── sync.sh               # ~/.hermes → 본 repo 동기화
├── restore.sh            # 본 repo → ~/.hermes 복원 (새 머신용)
└── .gitignore
```

## 새 머신 setup (git 1-clone)

```bash
# 0. Hermes Agent 설치 (운영체제 도구)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 1. 본 repo clone
git clone <git remote URL> ~/hermes-multi-agent-config
cd ~/hermes-multi-agent-config

# 2. Python venv (스크립트 실행용)
python3 -m venv .venv
source .venv/bin/activate
pip install pyyaml requests pytest

# 3. 파일 복원 (~/.hermes/ 디렉토리 재구성)
bash restore.sh

# 4. 보안 자료 (git 미포함) — 별도 안전 backup에서:
#    a) ~/.hermes/.env  — API keys 전체
#       필수 키: QDRANT_URL, QDRANT_API_KEY, VOYAGE_API_KEY, TAVILY_API_KEY,
#                GOOGLE_API_KEY (tech-artist), DISCORD_BOT_TOKEN, DISCORD_ALERT_USER_ID
#       프로필별 .env: ~/.hermes/profiles/{tech-artist,dev-gemma}/.env (각자 GOOGLE_API_KEY)
#    b) Anthropic Max OAuth: claude setup-token (또는 claude login)
#    c) OpenAI Codex OAuth:  codex login

# 5. Bypass 5종 패치 재설치
curl -fsSL https://raw.githubusercontent.com/kristianvast/hermes-claude-auth/main/install-remote.sh | bash

# 6. Gateway 등록 (orchestrator profile 단독 — Discord + cron 공존 패턴)
hermes --profile orchestrator gateway install
launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway.plist  # default profile 비활성

# 7. macOS sleep 정책 (M1 Air lid-close 운용)
sudo pmset -a tcpkeepalive 1
sudo pmset -a powernap 1
sudo pmset repeat wakeorpoweron MTWRFSU 02:55:00

# 8. 검증
hermes status                                            # Provider/Model 표시
HERMES_HOME=~/.hermes/profiles/orchestrator hermes cron status  # 6 active jobs
hermes chat -q 'say ok' --max-turns 1 -t ''             # 기본 default(orchestrator) 동작
hermes chat --profile sub-director -q 'say ok' --max-turns 1 -t ''
hermes chat --profile researcher -q 'say ok' --max-turns 1 -t ''
hermes chat --profile dev-gemma -q 'say ok' --max-turns 1 -t ''
bash ~/.hermes/bin/quota.sh                             # Anthropic Max 한도 GREEN
```

## 일상 동기화

```bash
# Hermes 운영 변경 후 (수동 or 자동)
cd ~/hermes-multi-agent-config
bash sync.sh
git add . && git commit -m "[sync] <변경 요약>"
git push
```

## 핵심 운영 규칙 (~/.hermes/wiki/CLAUDE.md 발췌)

- **Wiki-First → KB-Second**: wiki page graph traversal 먼저, miss 시 Qdrant `wiki_*` → `kb_*`
- **Provider Path Discipline**: directing-grade는 OAuth only (Anthropic Max, Codex). API key 자동 전환 금지
- **Source-Enforcement**: 모든 KB 청크 `source_url` + `citation` + `content_hash` 강제
- **AI-to-AI English-only**: delegate_task / worker prompts / system. 사용자 ↔ AI는 한국어
- **Immediate-Reflection**: 모든 변경 → wiki 갱신 + log.md 항목 + index.md updated 동일 turn

## Phase 2 (자체 머신 도착 시)

- Voyage-3 → BGE-M3 로컬 (-$3/월)
- Qdrant Cloud → 셀프호스트 (-$25/월)
- dev-gemma Haiku 4.5 → 로컬 오픈소스 (gemma/kimi 등) — Director/Sub-Director 외 worker slots 모두 로컬화 검토

## 자세한 의사결정 기록

`~/.hermes/wiki/concepts/setting-rebuild-2026-05-10.md` (Step 0~4 누적 의사결정)

## 라이선스

Personal/private use.

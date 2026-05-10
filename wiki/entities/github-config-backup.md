---
title: GitHub Config Backup
created: 2026-05-03
updated: 2026-05-03
type: entity
tags: [open-source, git, backup]
sources:
  - "https://github.com/luvear1203/hermes-config (Private)"
  - "~/.hermes/.gitignore"
confidence: high
---

# GitHub Config Backup

Hermes Agent 설정을 Git으로 관리하여 새 컴퓨터에서도 즉시 복원 가능.

## Repository

- URL: `https://github.com/luvear1203/hermes-config`
- Visibility: **Private**
- Location: `~/.hermes/` (디렉토리 자체가 Git 저장소)

## Git 추적 대상

- `.gitignore`, `.env.example`
- `SOUL.md`, `config.yaml`, `README.md`
- `profiles/*/config.yaml`, `profiles/*/SOUL.md`
- `wiki/**/*.md`

## Git 제외 대상

- `.env` — 실제 API 키
- `sessions/`, `logs/` — 세션 및 로그
- `state.db*` — 상태 데이터베이스
- 번들 스킬 (`skills/apple/`, `skills/creative/`, 등)
- `wiki/raw/assets/*.{png,jpg,pdf}` — 큰 바이너리

## 복원 절차

```bash
# 1. Hermes 설치 (번들 스킬 자동 설치)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# 2. 설정 clone
mv ~/.hermes ~/.hermes.bak
git clone https://github.com/luvear1203/hermes-config.git ~/.hermes

# 3. .env 설정
cp ~/.hermes/.env.example ~/.hermes/.env
# 실제 API 키 입력

# 4. Discord Gateway (선택)
orchestrator gateway setup
```

## Related

- [[multi-agent-system]]
- [[discord-gateway]]

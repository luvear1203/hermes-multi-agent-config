---
title: "Claude Auth Bypass (hermes-claude-auth)"
created: 2026-05-04
updated: 2026-05-04
type: entity
tags: [hermes, anthropic, oauth, bypass, subscription]
sources:
  - "https://github.com/kristianvast/hermes-claude-auth"
  - "~/.hermes/patches/anthropic_billing_bypass.py"
confidence: high
---

# Claude Auth Bypass

`kristianvast/hermes-claude-auth` — Hermes Agent에서 Claude Max/Pro 구독 OAuth를 정상 작동시키는 Python import hook 바이패스.

## 배경

2026-04-04 Anthropic이 서드파티 OAuth 요청을 서버사이드에서 차단. Hermes의 `build_anthropic_kwargs()`가 Claude Code와 다른 요청 형태를 보내서 감지됨. 이 바이패스는 Hermes 소스를 수정하지 않고 import hook으로 요청을 Claude Code 형태로 변환.

## 설치

```bash
curl -fsSL https://raw.githubusercontent.com/kristianvast/hermes-claude-auth/main/install-remote.sh | bash
```

## 제거

```bash
cd ~/.hermes/hermes-agent/hermes-claude-auth
./uninstall.sh          # hook만 제거
./uninstall.sh --purge  # hook + 패치 파일 제거
```

## 파일 구조

```
~/.hermes/patches/anthropic_billing_bypass.py       ← 패치 로직 본체
<hermes-venv>/site-packages/sitecustomize.py        ← MetaPathFinder import hook
~/.claude/.credentials.json                         ← Keychain→파일 미러링 (자동)
```

## 작동 원리

Hermes 인터프리터 시작 시 `sitecustomize.py`가 로드됨 → `anthropic_adapter.build_anthropic_kwargs`를 몽키패치:

1. **빌링 헤더**: SHA-256 서명된 `x-anthropic-billing-header`를 `system[0]`에 주입
2. **시스템 프롬프트**: non-identity 항목을 첫 user 메시지의 `<system-reminder>` 블록으로 재배치
3. **툴 이름**: `mcp_bash` → `mcp_Bash` (PascalCase 변환, 요청 시 rewrite, 응답 시 unhook)
4. **Beta**: `prompt-caching-scope-2026-01-05` 추가
5. **Temperature**: Opus 4.6 adaptive thinking 시 non-default temperature 제거

## 자동 유지보수

크론 job `claude-auth-bypass-check`가 매일 repo 업데이트 확인 후 자동 적용.

```bash
# 수동 확인
cd ~/.hermes/hermes-agent/hermes-claude-auth && git fetch && git log HEAD..origin/main

# 수동 업데이트
curl -fsSL https://raw.githubusercontent.com/kristianvast/hermes-claude-auth/main/install-remote.sh | bash
```

## 검증

```bash
hermes chat -q "say ok" -m claude-opus-4-7 --provider anthropic -Q
# 성공 시 출력: ok
# 실패 시: "out of extra usage" 또는 HTTP 429
```

## 호환성

- hermes-agent (Python 3.11+)
- Linux / macOS
- `build_anthropic_kwargs(is_oauth=...)` 인터페이스에 의존 → Hermes 업데이트 시 재검증 필요

## 관련

- [[hermes-max-integration]] — 전체 Claude Max 연동 구조
- [[multi-agent-system]] — 멀티 에이전트 시스템
- [GitHub: kristianvast/hermes-claude-auth](https://github.com/kristianvast/hermes-claude-auth)
- [Hermes Issue #17169](https://github.com/NousResearch/hermes-agent/issues/17169)

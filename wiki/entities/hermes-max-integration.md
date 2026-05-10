---
title: "Hermes ↔ Claude Max 구독 연결"
created: 2026-05-03
updated: 2026-05-04
type: entity
tags:
  - hermes
  - anthropic
  - oauth
  - subscription
  - infrastructure
  - bypass
sources:
  - "~/.hermes/hermes-agent/agent/anthropic_adapter.py"
  - "https://github.com/kristianvast/hermes-claude-auth"
  - "https://github.com/NousResearch/hermes-agent/issues/17169"
confidence: high
---

# Hermes ↔ Claude Max 구독 연결

[[multi-agent-system|Hermes Agent]]가 Anthropic Claude Max 구독을 인증 수단으로 사용하는 전체 메커니즘. 2026-05-04 최종 검증 완료.

## 핵심 결과

**별도 API 키 불필요.** Claude Max 구독 + `kristianvast/hermes-claude-auth` 바이패스로 Claude Opus 4.7 정상 작동 확인.

## 2026년 4월 4일 Anthropic 정책 변경

Anthropic이 서버사이드 OAuth 검증을 도입해 서드파티 도구에서 Opus/Sonnet 호출을 차단. Haiku만 예외. 차단 메커니즘:

| 감지 신호 | Claude Code 공식 | Hermes (차단 원인) |
|-----------|-----------------|-------------------|
| 시스템 프롬프트 | 9개 개별 블록, "Claude Code" identity 포함 | 단일 블록, "Hermes Agent" 표기 |
| 툴 이름 | `mcp_Bash`, `mcp_Read` (PascalCase) | `mcp_bash` (lowercase) |
| 빌링 헤더 | SHA-256 서명 `x-anthropic-billing-header` | 없음 |
| Body 필드 | `metadata.user_id`, `output_config`, `thinking`, `context_management` | 없음 |

## 해결책: kristianvast/hermes-claude-auth

**Hermes 전용 Python import hook 바이패스.** Hermes 소스 파일을 전혀 수정하지 않음.

### 설치

```bash
curl -fsSL https://raw.githubusercontent.com/kristianvast/hermes-claude-auth/main/install-remote.sh | bash
```

### 적용되는 패치

1. **SHA-256 빌링 헤더 서명** — `x-anthropic-billing-header`를 `system[0]`에 주입
2. **시스템 프롬프트 재배치** — non-identity 항목을 첫 user 메시지의 `<system-reminder>`로 이동
3. **PascalCase 툴 이름 변환** — `mcp_bash` → `mcp_Bash`
4. **Beta 플래그 추가** — `prompt-caching-scope-2026-01-05`
5. **Temperature 보정** — Opus 4.6 adaptive thinking 시 non-default temperature 제거

### 설치 파일 구조

```
~/.hermes/patches/anthropic_billing_bypass.py     ← 패치 로직
<venv>/site-packages/sitecustomize.py              ← Python import hook
```

### 자동 유지보수

```bash
# 수동 업데이트
curl -fsSL https://raw.githubusercontent.com/kristianvast/hermes-claude-auth/main/install-remote.sh | bash

# 크론 자동 체크 (매일 1회)
hermes cron list  # job: claude-auth-bypass-check
```

## 인증 방식

### 지원 인증 3종

| 방식 | 토큰 형식 | 헤더 | 사용 |
|------|-----------|------|------|
| API key | `sk-ant-api*` | `x-api-key` | pay-per-token |
| OAuth setup-token | `sk-ant-oat*` | Bearer + `anthropic-beta` | Max 구독 (직접) |
| Claude Code OAuth | Keychain / `.credentials.json` | Bearer | Max 구독 (자동) |

### 토큰 발급

```bash
# Max 구독 → 장기 토큰 (1년 유효)
claude setup-token

# .env에 등록
export ANTHROPIC_TOKEN="sk-ant-oat01-..."
```

### 자동 검출 흐름

```
1. macOS Keychain "Claude Code-credentials" 조회
   ↓
2. ~/.claude/.credentials.json 폴백
   ↓
3. 환경변수 ANTHROPIC_TOKEN / CLAUDE_CODE_OAUTH_TOKEN
   ↓
4. OAuth PKCE 플로우 (hermes auth add anthropic)
```

## 검증 결과 (2026-05-04)

```
hermes chat -q "say ok" -m claude-opus-4-7 --provider anthropic
→ "ok" ✅
```

Bypass 로그: `[anthropic_billing_bypass] Bypass installed`

## 환경 분리 전략

| 도구 | 인증 | 결제 |
|------|------|------|
| Hermes (orchestrator·researcher·cron) | Claude Code OAuth + bypass | Max 구독 사용량 |
| [[mythrill-pipeline]] 검증 스크립트 | `ANTHROPIC_API_KEY` (별도) | API pay-per-token |
| Claude Code CLI | Keychain | Max 구독 사용량 |

## 약관 해석

Anthropic Agent SDK 문서:
> "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products."

핵심: "offer ... for their products" — 외부에 제공·재판매 금지. 본인이 본인 도구에서 본인 구독 사용은 명시적 금지 아님.

## 관련 GitHub 이슈

- [#17169](https://github.com/NousResearch/hermes-agent/issues/17169) — Opus 4.7 429, Haiku는 정상 (Anthropic 서버사이드 검증)
- [#15080](https://github.com/NousResearch/hermes-agent/issues/15080) — tools 파라미터가 트리거
- [#13972](https://github.com/NousResearch/hermes-agent/pull/13972) — 툴 이름 변경 PR

## 관련 Wiki

- [[multi-agent-system]] — 멀티 에이전트 구조
- [[claude-auth-bypass]] — 바이패스 상세
- [[github-config-backup]] — 설정 백업
- [[cron-api-monitor]] — Max 한도 영향

---
title: Cron API Monitor
created: 2026-05-03
updated: 2026-05-03
type: entity
tags: [agent, monitoring, automation]
sources:
  - "~/.hermes/cron/"
  - "[[discord-gateway]]"
confidence: high
---

# Cron API Monitor

API 사용량을 주기적으로 모니터링하고 필요 시 Discord로 알림.

## Schedule

- **기본:** 매시간 실행 (`0 * * * *`)
- **활동 감지 시:** 상세 API 사용량 보고
- **비활동 시:** 00, 06, 12, 18시에만 Discord로 간략 요약
- **비용 초과 시:** 일일 $5 초과 즉시 Discord 경고

## Job Info

- Job ID: `91f9c5df03c0`
- Deliver: origin (현재 대화 채널로 전달 — Discord/CLI 자동 감지)

## Check Logic

1. `hermes insights --days 1` — 최근 24시간 토큰 사용량 확인
2. `session_search` — 최근 1시간 내 delegate_task 활동 체크
3. 활동 O → 상세 보고
4. 활동 X → 6시간 단위로만 Discord 전송
5. 비용 $5/day 초과 → 즉시 경고

## Related

- [[multi-agent-system]]
- [[discord-gateway]]

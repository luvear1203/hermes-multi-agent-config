---
title: Discord Gateway
created: 2026-05-03
updated: 2026-05-03
type: entity
tags: [agent, messaging, discord]
sources:
  - "~/.hermes/profiles/orchestrator/platforms/discord/"
  - "https://discord.com/developers/docs/topics/gateway"
confidence: high
---

# Discord Gateway

Hermes Agent를 Discord 봇으로 연결하여 어디서나 에이전트와 대화하고 알림을 수신.

## Setup

### 1. Discord Developer Portal

- https://discord.com/developers/applications → New Application
- Bot → Privileged Gateway Intents:
  - ✅ PRESENCE INTENT
  - ✅ SERVER MEMBERS INTENT
  - ✅ **MESSAGE CONTENT INTENT** (필수!)

### 2. OAuth2 URL 생성

- Scopes: `bot`, `applications.commands`
- Permissions: Send Messages, Read Messages, Read Message History, Send Messages in Threads, Use Slash Commands, Add Reactions, Embed Links, Attach Files

### 3. Hermes 설정

```bash
# .env에 토큰 추가
echo 'DISCORD_BOT_TOKEN=MT...' >> ~/.hermes/profiles/orchestrator/.env

# Gateway 설치 및 시작
orchestrator gateway install
orchestrator gateway start
```

### 4. 홈 채널 설정

```bash
echo 'DISCORD_HOME_CHANNEL=<channel_id>' >> ~/.hermes/profiles/orchestrator/.env
orchestrator gateway restart
```

## Current Status

- Gateway: ✅ Running
- Bot: Hermes Orchestra#5906
- Home Channel: `1500178987383656478`

## Security

⚠️ 토큰 유출 시 즉시 Discord Developer Portal에서 Reset Token

## Related

- [[multi-agent-system]]
- [[cron-api-monitor]]

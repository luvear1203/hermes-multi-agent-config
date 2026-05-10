---
title: Idea Validation Pipeline
created: 2026-05-03
updated: 2026-05-03
type: entity
tags: [multi-agent, research, ideation]
sources:
  - "~/.hermes/skills/autonomous-ai-agents/idea-validation-pipeline/SKILL.md"
  - "[[multi-agent-system]]"
confidence: high
---

# Idea Validation Pipeline

사용자 아이디어를 자동으로 검증하는 멀티 에이전트 파이프라인 스킬.

## Workflow

1. **아이디어 분석** — 핵심 가치, 기술 스택, 타겟 사용자 파악
2. **선행연구 조사** — Researcher(Claude)가 arXiv, GitHub 검색
3. **중복/차별점 분석** — 유사 프로젝트 존재 여부, 차별화 가능성
4. **보고서 작성** — 마크다운 형식으로 사용자에게 제시
5. **개발 계획** — 진행 가능 시 Kanban 태스크로 분배

## Skill Location

`~/.hermes/skills/autonomous-ai-agents/idea-validation-pipeline/SKILL.md`

## Usage

Orchestrator에게 아이디어를 던지면 자동 실행됨:
```
"AI 기반 실시간 코드 리뷰 도구를 만들고 싶어"
→ Researcher가 논문 검색
→ 결과 취합 후 보고
→ 개발 가능하면 Dev-Gemma에 위임
```

## Related

- [[multi-agent-system]]
- [[roles]] · [[cost-tiers]]
- [[graphify-setup]]

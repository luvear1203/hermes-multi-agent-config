---
title: LLM Wiki Setup
created: 2026-05-03
updated: 2026-05-03
type: concept
tags: [wiki, knowledge-base, markdown]
sources:
  - "https://karpathy.ai (LLM Wiki concept)"
  - "[[graphify-setup]]"
confidence: high
---

# LLM Wiki Setup

Karpathy 패턴 기반 LLM Wiki. WIKI_PATH=~/.hermes/wiki 로 Git에 포함되어 백업됨.

## Structure

```
~/.hermes/wiki/
├── SCHEMA.md          # 도메인 규칙 (AI/ML, 멀티에이전트)
├── index.md           # 전체 카탈로그
├── log.md             # 작업 기록
├── raw/               # 원본 자료 (불변)
├── entities/          # 개체 페이지
├── concepts/          # 개념 페이지
├── comparisons/       # 비교 분석
└── queries/           # 질문 결과
```

## Conventions

- 파일명: lowercase-hyphens
- 모든 페이지 YAML frontmatter 필수
- `[[wikilinks]]`로 교차 참조 (페이지당 최소 2개)
- 수정 시 `updated` 갱신
- 모든 작업 `log.md`에 기록

## Tag Taxonomy

- **AI/ML**: model, architecture, benchmark, training
- **Multi-Agent**: agent, orchestration, delegation, multi-agent
- **Tools**: open-source, framework, CLI
- **Research**: paper, arxiv, survey
- **Meta**: comparison, timeline, idea

## Integration

- `~/.hermes/.env` → `WIKI_PATH=~/.hermes/wiki`
- Git에 자동 포함 (clone 시 복원)
- Obsidian으로 열면 그래프 뷰 지원
- [[Graphify]] 추가 시 시각화 강화

## Related

- [[multi-agent-system]]
- [[github-config-backup]]

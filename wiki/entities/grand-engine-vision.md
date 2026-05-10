---
title: Grand Engine Vision — 자연어 생성 자체 게임 엔진 대장정
created: 2026-05-04
updated: 2026-05-07
type: entity
tags: [project, vision, engine, multi-agent]
sources:
  - "사용자 구두 비전 진술 (2026-05-04 세션)"
  - "[[mythrill-pipeline]]"
  - "[[mythrill-roadmap]]"
confidence: high
---

# Grand Engine Vision

사용자(luvear1203)가 단일 개발자로서 추진하는 최종 목표.
**자연어로 게임을 생성하는 독자 게임 엔진 구축**이며,
[[mythrill-pipeline]]은 그 대장정의 첫 시발점이다.

## 대장정 단계

| 순서 | 코드네임 | 범위 | 상태 |
|---|---|---|---|
| 1 | [[mythrill-pipeline]] | 자연어 → VFX 파라미터 (MPM 솔버 기반) | 진행 중 |
| 2 | Adamantium | (미정) | 미정 |
| 3+ | 추가 프로젝트 | (미정) | 미정 |
| Final | 통합 자체 게임 엔진 | 전 단계 산출물 통합 | 장기 목표 |

각 단계의 산출물은 단일 제품이 아니라 **최종 통합 엔진의 컴포넌트**가 된다.
Mythrill의 LLM 분리 설계 → 통합 엔진의 자연어 입력 레이어.
Mythrill의 MPM 솔버 → 통합 엔진의 시뮬레이션 모듈.

## 통치 원칙

- 단계별 산출물은 즉시 출시 가능하되, 통합 엔진 흡수를 가로막는 결합은 금지
- 새 코드네임 프로젝트는 [[roles]]의 Engine Architect 승인 필요 (현재는 Director 겸임)
- 각 단계 종료 시 [[validators]] 패턴으로 통합 가능성 검증

## 멀티에이전트 운영

이 비전은 단일 개발자가 LLM 멀티에이전트 스튜디오를 통해 추진한다.
조직 구조: [[roles]] · 비용 등급: [[cost-tiers]] · 모델 갱신 정책: [[model-prompting-conventions]]

운영 제어판은 [[local-agent-control-plane]]으로 분리한다. Hermes/OpenClaw/Codex는 실행 런타임으로 유지하고,
Mission Board·승인 대기열·context preview·run log·knowledge write review는 별도 로컬 앱에서 관리한다.

## 관련 문서

- [[mythrill-pipeline]] · [[mythrill-roadmap]] · [[mythrill-architecture]]
- [[multi-agent-system]] · [[local-agent-control-plane]] · [[roles]] · [[cost-tiers]]

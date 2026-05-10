---
title: "Naked 뷰어"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - ux
  - viewer
  - python
  - validation
sources:
  - "~/Downloads/도전제안서_수정본.docx"
confidence: high
---

# Naked 뷰어

[[ai-rookie-2026]] 도전제안서 2.2의 차별점 ②. 베이크 출력 *전*에 사용자가 결과물을 미리 검토할 수 있는 Python 기반 사전 확인 메커니즘.

## 정의

**Naked = "날 것"**. 빛·머티리얼·포스트프로세싱이 거의 입혀지지 않은 시뮬레이션 결과 그대로를 재생하는 뷰어. [[mythrill-architecture]] 7단계 (사용자 확인 ②) UI의 핵심 구현체.

## 두 가지 검토 모드

| 모드 | 환경 | 보여주는 것 |
|------|------|-------------|
| **Naked 모드** | Python 자체 뷰어 | 빛·셰이더 거의 없는 입자/볼륨 거동 그대로 |
| **Lit 모드** | 언리얼 연동 (Nanite + Lumen) | 실제 게임 환경에서의 최종 시각 |

두 모드를 모두 검토할 수 있어 사용자가 *물리 거동의 자연스러움*과 *최종 시각 결과물*을 분리해 판단 가능.

## 위치 in 시스템

```
시뮬레이션 결과 + 시각 오버레이
    ↓
[Naked 뷰어] ← 사용자 확인 ②
    ├─ Yes → 베이킹
    └─ No-A/B/C → 3분기 회귀 ([[three-branch-regression]])
```

## 가치

### 베이크 비용 절감
베이크는 시스템에서 가장 비싼 단계 중 하나. Naked 단계에서 거동·시각이 잘못된 결과를 걸러내면 베이크 낭비 차단.

### 모드 분리로 판단 정확도 향상
- Naked 모드: "물리 거동 자체가 이상한가?" → No-B (LLM ② 재실행) 판정
- Lit 모드: "거동은 맞는데 색·발광이 이상한가?" → No-C (시각 오버레이만 재실행) 판정

이 모드 분리가 [[three-branch-regression]]의 No-B / No-C 분기 진입을 자연스럽게 만듦.

### 디자이너 직관 통제
"날것"을 본 후 "최종"을 비교하면, 셰이더가 가린 거동의 어색함이 드러남. 디자이너는 베이크된 결과만 보면 셰이더의 시각 압도에 속아 거동 결함을 놓침.

## 구현 의도

- **Python 기반**: MVP 단계 핵심 UI를 게임 엔진에 묶지 않고 독립 실행 → [[mythrill-roadmap]] Phase 3(자체 에디터 GUI) 진화의 시드
- **언리얼 연동**: Nanite·Lumen으로 최종 게임 환경 시뮬레이션 (별도 프로세스/플러그인)

## 한계 / 미정 사항

- Lit 모드에서 언리얼 외 엔진(유니티 등)은 Phase 2 이후 ([[mythrill-roadmap]])
- Naked 모드에 어디까지 시각 요소를 노출할지 (예: 알베도만? 발광까지?) 미정
- Lit 모드에 사용자가 자체 머티리얼/라이트를 주입할 수 있는지 미정

## 관련 Wiki 페이지

- [[mythrill-mvp-scope]] — MVP에서 Naked 뷰어가 차지하는 위치
- [[ai-rookie-2026]] — 도전제안서 2.2 차별점 ②
- [[mythrill-architecture]] — 7단계 사용자 확인 ②의 UI
- [[three-branch-regression]] — Naked·Lit 모드 분리가 매개하는 No-B/No-C 분기
- [[pre-bake-vfx-workflow]] — 베이크 비용 절감의 의의

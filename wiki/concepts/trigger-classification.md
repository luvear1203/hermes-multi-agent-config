---
title: "트리거 4종 분류"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - llm
  - prompt-engineering
  - trigger
sources:
  - "~/mythrill-pipeline/prompts/llm1_intent.md"
confidence: high
---

# 트리거 4종 분류

[[stage-separation-rule]]에서 단계가 분리될 때, **분리의 원인**을 4종 중 하나로 명시. LLM ① 출력의 `stages[].trigger` 필드에 들어감.

## 4종

| 트리거 | 물리적 의미 | 예시 거동 |
|---|---|---|
| **시간 (time)** | 시간 의존 상전이, 자발적 변화 | 응결·결정화·화학 반응 진행 |
| **위치 (position)** | 공간상 경계 도달, 경계 조건 변화 | 지면 충돌·벽 부딪힘·결계 통과 |
| **온도 (temperature)** | 열역학적 상전이 | 결빙·융해·증발 |
| **외력 (force)** | 외부 에너지 입력으로 인한 거동 종류 전환 | 충격에 의한 파괴·압축에 의한 상전이 |

이 4종이 연속체역학에서 거동 변화를 일으키는 원인을 커버. 다른 트리거(분위기·감정 등)는 물리적으로 정의 불가 → 솔버 입력 불가.

## 트리거 vs 비트리거 판정

각 트리거가 진짜 단계 분리 사유인지 검증.

### 시간 트리거

- 진짜: "흘러내리다 굳는 송진" — 시간이 지나며 상전이 발생
- 가짜: "천천히 모이다 압축되는 구체" — 같은 수렴 거동의 강도 변화 ([[stage-separation-rule]] (c))

### 위치 트리거

- 진짜: "땅에 떨어져 튀어오르는 점액" — 자유낙하 → 반발 충돌, regime 전환
- 가짜: 단순 이동·도달만 있는 경우, 별도 거동 발생 안 하면 1단계

### 온도 트리거

[[stage-separation-rule]] (b) 참조. 명시적 상전이 필요. 단순 색 변화는 트리거 아님.

### 외력 트리거

[[stage-separation-rule]] (a) 참조. 외력의 *시작*은 트리거 아님. 외력 후 거동 종류가 바뀌어야 함.

[[llm1-validation]]에서 50개 입력 중 외력 트리거 진짜인 건 1건 (#34 망치→도자기) (출처: [[llm1-validation]] v3 50건 카테고리). 다른 4건은 외력 시작점에 불과 → 1단계로 재분류.

## 트리거 표기 규칙

`stages[].trigger` 필드에 한국어로 직접 기술:

- `"시간 경과"` (time)
- `"지면 도달"`, `"결계 통과"` (position)
- `"냉각 임계 도달"`, `"가열"` (temperature)
- `"충돌"`, `"외력 인가"` (force)

1단계 거동의 첫 stage_id에는 `trigger: null`.

## 카테고리와의 관계

[[llm1-validation]]의 50입력은 트리거 종류로 분류됨:

| 카테고리 | 트리거 |
|---|---|
| `2stage_time` | 시간 |
| `2stage_position` | 위치 |
| `2stage_temp` | 온도 |
| `2stage_force` | 외력 (진짜 거동 전환) |
| `1stage_*` | 트리거 없음 |
| `3stage_plus` | 트리거 2회 이상 (혼합) |

## 관련 Wiki 페이지

- [[stage-separation-rule]] — 단계 분리 룰 본체
- [[visual-inference-policy]] — visual 필드 별도 정책
- [[vfx-input-labeling-guide]] — 트리거 분류를 라벨링에 적용
- [[llm1-validation]] — 트리거 분류 정확도 검증

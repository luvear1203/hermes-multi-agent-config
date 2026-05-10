---
title: "Visual 추론 정책"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - llm
  - prompt-engineering
  - visual
sources:
  - "~/mythrill-pipeline/prompts/llm1_intent.md"
confidence: high
---

# Visual 추론 정책

LLM ① 출력의 `visual` 필드에 대한 정책. **시각 정보가 명시되지 않아도 합리적 추론이 가능하면 채우되 추론임을 명시**.

## 배경

초기 결정(Decision 4 v1): "직접 명시된 시각 단어만 visual에 채움". 학습 편향 차단 목적.

이후 발견: "화염 → 붉은", "용암 → 주황", "마나 → 푸른"은 **편향이 아니라 인류 공통 상식**. 이걸 막는 건 LLM의 강점을 죽이는 것.

## 개정 정책 (Decision 4 v2)

| 단서 종류 | 처리 | inferred 플래그 |
|---|---|---|
| 직접 명시 | visual 채움 | `false` |
| 합리적 추론 가능 | visual 채움 | `true` |
| 단서 없음 | `visual: null` | — |

## visual 필드 스키마

```json
"visual": {
  "color_keywords": [str],
  "emission": str | null,
  "inferred": bool,
  "inferred_from": str | null
} | null
```

- `inferred: false`이면 `inferred_from: null`
- `inferred: true`이면 `inferred_from`에 추론 단서 단어 (예: `"화염"`)

## 단서 분류 예시

### 직접 명시

키워드: 푸른·붉은·검은·노란·황금·은빛 / 빛나는·발광·반짝이는 / 투명·반투명

```
입력: "푸른 빛을 내며 흩어지는 마나 가루"
→ color_keywords: ["푸른"], emission: "발광", inferred: false
```

### 합리적 추론

키워드: 화염·용암·마나·얼음·번개·그림자·어둠·신성·쇳물

```
입력: "용암 동굴 천장에서 흘러내리는 마그마"
→ color_keywords: ["주황", "붉은"], emission: "발광",
  inferred: true, inferred_from: "용암"
```

### 단서 없음

```
입력: "검을 휘두를 때 발생하는 잔상"
→ visual: null
```

## 카테고리 활용

[[llm1-validation]]의 50입력 중 1단계 입력은 시각 단서로 세분화 (출처: [[llm1-validation]] v3 분포):

- `1stage_visual_direct` (9건): 직접 명시 단어 포함
- `1stage_visual_inferred` (7건): 추론 가능 단어 포함
- `1stage_no_visual` (10건): 시각 단서 전혀 없음

이 분류 자체가 정책 검증의 일부.

## 정책의 의의

- 사용자 검토 단계([[three-branch-regression]])에서 "내가 직접 말한 색인지, AI가 추론한 색인지" 구분 가능
- 추론한 색이 마음에 안 들면 색만 수정하는 부분 회귀 가능
- 일관성 유지 (추론 여부가 명시됨)

## 한계

- "검기" 같은 신화적 입력은 색이 정해지지 않아 추론 단서가 약함
- 같은 단어도 컨텍스트에 따라 다름 (예: "검은"이 색인지 검의 형용사인지)

## 관련 Wiki 페이지

- [[stage-separation-rule]] — 단계 룰과 함께 LLM ①의 두 축
- [[trigger-classification]] — 트리거 분류
- [[vfx-input-labeling-guide]] — 정책을 라벨링에 적용
- [[llm1-validation]] — 정책의 카테고리별 검증
- [[three-branch-regression]] — 사용자 확인 ① 후 분기

---
title: "VFX 입력 라벨링 가이드"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - llm
  - labeling
  - workflow
sources:
  - "~/mythrill-pipeline/tests/inputs.txt"
  - "~/mythrill-pipeline/tests/analyze_results.py"
confidence: high
---

# VFX 입력 라벨링 가이드

게임 제작 실사용 또는 검증 데이터 확장 시, 새 자연어 입력에 카테고리 라벨을 부여하는 절차. v3 검증 ([[llm1-validation]]) 라벨 정렬 작업에서 도출.

## 라벨 형식

```python
input_id: (category, expected_stage_count)
```

- `category`: 9종 중 하나
- `expected_stage_count`: 0·1·2·3+

## 결정 트리

새 입력을 받으면 다음 순서로 판정 (v3 50건 라벨 정렬 결과는 출처: [[llm1-validation]]).

### Step 1: 입력이 물리 거동을 묘사하는가

NO → `edge_case`, 0단계
- 의미 없는 텍스트 ("asdfghjkl")
- 비물리적 추상 ("사랑은 무엇일까")
- 입력 부족 ("그냥 멋있는 거")
- 행위 중심 명령 ("점심 뭐 먹지")

YES → Step 2

### Step 2: 거동 전환이 있는가

[[stage-separation-rule]]의 결정 절차 적용.

질문 순서:
1. 응력 모델(구성방정식)이 바뀌는가?
2. 지배 force regime이 바뀌는가?

둘 다 NO → 1단계 (Step 3로)
하나라도 YES → 다단계 (Step 4로)

### Step 3 (1단계인 경우): 시각 단서 종류

[[visual-inference-policy]] 참조.

| 단서 | 카테고리 |
|---|---|
| 직접 명시 (푸른·빛나는 등) | `1stage_visual_direct` |
| 추론 가능 (화염·용암 등) | `1stage_visual_inferred` |
| 단서 없음 | `1stage_no_visual` |

### Step 4 (다단계인 경우): 트리거 종류 + 단계 수

#### 단계 수

거동 전환 횟수 + 1.

전환 ≥ 2 → `3stage_plus`, 단계 수 = 전환 + 1

전환 = 1 → 2단계, 트리거 종류로 분기:

| 트리거 ([[trigger-classification]]) | 카테고리 |
|---|---|
| time | `2stage_time` |
| position | `2stage_position` |
| temperature | `2stage_temp` |
| force | `2stage_force` (외력이 *진짜* 거동을 바꾼 경우만) |

## 함정 케이스

라벨이 어긋나기 쉬운 패턴 (v1→v3에서 재정렬된 9건 분석).

### 함정 1: 외력 시작점을 트리거로 오인

```
"주문을 외우자 솟구치는 화염"
틀림: 2stage_force (주문 → 화염)
맞음: 1stage_visual_direct (주문 = 시작점, 솟구침이 1거동)
```

[[stage-separation-rule]] (a) 참조. 외력 트리거는 외력 *후* 거동 종류가 바뀌는 경우만.

### 함정 2: 강도 변화를 단계로 분리

```
"천천히 모이다 한 점에서 압축되는 에너지 구체"
틀림: 2stage_time (모임 → 압축)
맞음: 1stage_no_visual (수렴 거동의 강도 변화, [[stage-separation-rule]] (c))
```

### 함정 3: 종료 상태를 단계로 분리

```
"잉크가 가라앉다 퍼지고 균일하게 섞임"
틀림: 3stage_plus
맞음: 1stage_no_visual (전 구간 점성 유체, "균일" = 종료 상태)
```

### 함정 4: edge_case에 모호한 입력

```
"검기"
틀림: edge_case (입력 부족)
맞음: 1stage_no_visual (검기 = 검의 잔상으로 자연 해석 가능)
```

edge_case는 *명백히* 거부할 입력만. 모호하면 모델 해석을 따름.

### 함정 5: 색 변화 = 온도 트리거 오인

```
"열을 받아 색이 변하는 금속"
틀림: 2stage_temp
맞음: 1stage_visual_direct 또는 _inferred (거동 동일, 색만 변함, [[stage-separation-rule]] (b))
```

## 분포 균형

검증 데이터 수집 시 카테고리 간 균형 권장. v3 분포 (50건):

```
1stage_visual_direct  : 9
1stage_visual_inferred: 7
1stage_no_visual      : 10
2stage_time           : 7
2stage_position       : 6
2stage_force          : 1
2stage_temp           : 4
3stage_plus           : 1
edge_case             : 5
```

`2stage_force`와 `3stage_plus`가 적은 건 **현실에서 드문 패턴이라는 발견 자체**. 무리한 균형 맞추기 불필요.

## 분석 스크립트 반영

`~/mythrill-pipeline/tests/analyze_results.py`의 `CATEGORY_MAP` dict에 라벨 추가. 라벨만 바꾸면 동일 raw CSV에서 재분석 가능 (API 호출 0회).

```python
CATEGORY_MAP = {
    1: ("1stage_visual_direct", 1),
    2: ("1stage_visual_direct", 1),
    # ...
    51: ("새_카테고리", 단계수),  # 새 입력 추가
}
```

## 게임 제작 실사용 시

[[mythrill-rpg-showcase]] 작업 중 새 VFX를 자연어로 묘사할 때, 본 가이드로 카테고리 추정 → 해당 카테고리에 정확도 높은 모델 선택 ([[llm1-validation]]의 모델별 정확도 표 참조).

## 관련 Wiki 페이지

- [[stage-separation-rule]] — Step 2의 룰
- [[trigger-classification]] — Step 4의 트리거 분류
- [[visual-inference-policy]] — Step 3의 시각 단서 분류
- [[llm1-validation]] — 본 가이드의 도출 근거
- [[mythrill-rpg-showcase]] — 게임 제작 실사용 컨텍스트

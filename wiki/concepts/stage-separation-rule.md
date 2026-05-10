---
title: "단계 분리 룰 (R1)"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - llm
  - prompt-engineering
  - stage
sources:
  - "~/mythrill-pipeline/prompts/llm1_intent.md"
confidence: high
---

# 단계 분리 룰 (R1)

LLM ①이 자연어 입력에서 **단계(stage)를 몇 개로 분리할지 결정하는 룰**. v3 검증 ([[llm1-validation]]) 후 확정.

## 핵심 정의

> **단계 = 같은 물리 regime이 지배하는 시간 구간**

단계 분리 = MPM 솔버에서 [[mpm-constitutive-equation-swap|구성방정식 교체]] 시점 또는 지배 force regime 변경 시점.

## 단계 수 공식

```
단계 수 = 거동 전환 횟수 + 1
```

거동 전환의 정의:
1. 응력 모델(구성방정식) 교체 (예: 액체 → 고체 상전이)
2. 지배 force regime 변경 (예: 자유낙하 → 충돌반발)

**시작·끝·강도·속도 변화는 거동 전환이 아님 → 같은 단계로 흡수.**

## 결정 절차 (LLM ① 프롬프트에 명시)

```
After identifying behavior, ask in order:
1. Does the constitutive equation change? (e.g., 액체→고체)
2. Does the dominant force regime change? (e.g., 자유낙하→충돌반발)
If YES to either → separate into different stages.
If NO to both → it is 1 stage.
```

트리거 4종 분류는 [[trigger-classification]] 참조.

## 명확화 (a)~(d)

R1 룰의 모호점을 v2에서 명문화.

### (a) 외력은 자동 트리거가 아니다

외력의 *시작*은 거동의 시작점이지 regime 변경이 아님. 외력 *후* 거동 종류가 바뀌어야 단계 분리.

| 입력 | 단계 | 이유 |
|---|---|---|
| 주문을 외우자 발사되는 화염 | 1 | 주문 = 시작점, 발사 = 1거동 |
| 망치로 내려치자 부서지는 도자기 | 2 | 충돌 변형 → 파편 분산: regime 전환 |
| 입김을 불자 흩어지는 민들레 홀씨 | 1 | 입김 = 시작점, 흩어짐 = 1거동 |
| 누군가 잡아당기자 늘어나는 고무줄 | 1 | 외력 작용 = 거동 자체. 탄성 regime 유지 |

[[llm1-validation]]에서 50입력 중 외력 트리거 진짜인 건 1건 (#34) (출처: [[llm1-validation]] v3 라벨 분포).

### (b) 온도 트리거는 명시적 상전이 필요

"~에 닿아 변하는" 표현이 있어도 거동 종류가 실제로 바뀌어야 분리.

| 입력 | 단계 | 이유 |
|---|---|---|
| 빙결 마법에 닿아 얼어붙는 적 | 2 | 액체상 → 고체상 |
| 뜨거운 표면에 닿아 증발하는 물줄기 | 2 | 액체상 → 기체상 |
| 열을 받아 색이 변하는 금속 | 1 | 색만 변함, 거동 동일 |

### (c) 속도·강도 변화는 단계가 아니다

운동학적 페이즈(가속·정상·감속)는 같은 구성방정식 안에서 자연 발생.

| 입력 | 단계 | 이유 |
|---|---|---|
| 점점 빠르게 회전하는 입자 | 1 | 회전 강도만 변함 |
| 천천히 모이다가 한 점에서 압축되는 에너지 구체 | 1 | 수렴 거동의 강도 변화 |

### (d) 같은 regime의 거동 사슬은 1단계

"A하다가 B하는" 형식이라도 A·B가 같은 응력 모델로 처리되면 1단계.

| 입력 | 단계 | 이유 |
|---|---|---|
| 흘러내리며 퍼지는 액체 | 1 | 흐름·확산 모두 점성 액체 거동 |
| 흘러내리다가 굳는 송진 | 2 | 액체 → 고체 |
| 가라앉다 퍼지고 균일하게 섞이는 잉크 | 1 | 전 구간 점성 유체 |

## 룰의 검증 결과

| 단계 | 외력 정확도 | 평균 정확도 |
|---|---|---|
| v1 (룰 미명문화) | 0~40% | 76~85% |
| v3 (룰 명문화 + 라벨 재정렬) | 100% | 91.3% |

## 한계

- Claude는 본 룰보다 더 보수적으로 단계를 분리하는 경향 ([[llm1-validation]] 참조)
- "균일하게 섞임" 같은 종료 상태 묘사가 모델별로 다르게 해석됨
- 비물리적 단어("영체", "차원의 균열")에서 일부 모델 빈 응답

## 관련 Wiki 페이지

- [[trigger-classification]] — 4종 트리거 정의
- [[visual-inference-policy]] — visual 필드 별도 정책
- [[vfx-input-labeling-guide]] — 룰을 사용해 새 입력 라벨링하는 절차
- [[llm1-validation]] — 본 룰의 검증 결과
- [[mpm-constitutive-equation-swap]] — 단계 = 구성방정식 교체 시점
- [[llm-separation-design]] — LLM ①의 책임 범위

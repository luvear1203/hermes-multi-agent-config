---
title: "MPM 단일 솔버 동적 구성방정식 스왑"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - mpm
  - simulation
  - physics
  - constitutive-equation
  - solver
sources:
  - "~/.hermes/wiki/raw/obsidian-vault/Brain/Mythrill_파이프라인/00_시스템코어/아키텍처_v1_0.md"
confidence: high
---

# MPM 단일 솔버 동적 구성방정식 스왑

Mythrill 파이프라인의 물리 시뮬레이션 핵심 전략. 다중 솔버를 stitch하지 않고, **MPM 단일 솔버 위에서 입자별로 구성방정식을 동적으로 교체**하는 방식.

## 설계 근거

- 두 솔버를 stitch하면 입자 데이터 전달·경계 처리에서 불일치 발생
- MPM은 입자별 상태(phase)를 들고 있으므로, 임계 조건 도달 시 구성방정식만 교체하면 자연스러운 상전이 표현 가능
- 알로에젤(비뉴턴 액체) → 촛농(고체화) 같은 시나리오를 한 솔버 안에서 처리

## 주요 구성방정식

### Carreau-Yasuda 모델 (비뉴턴 유체)
```
η(γ̇) = η_∞ + (η_0 - η_∞) · [1 + (λγ̇)^a]^((n-1)/a)
```

| 파라미터 | 의미 | 판타지 매핑 |
|----------|------|------------|
| η_0 | 저전단 점성 | 정지 시 점성 |
| η_∞ | 고전단 점성 | 빠른 흐름 시 점성 |
| λ | 시간 상수 | 전이 속도 |
| n | 멱지수 | n<1: 전단박화 / n>1: 전단증화 |
| a | Yasuda 계수 | 전이 곡선 형태 |

### Arrhenius 식 (온도 의존 점성)
```
μ(T) = μ_0 · exp(E_a / RT)
```
저온에서 점성 폭증 → 촛농의 응고 거동.

### Enthalpy 방법 (상전이)
```
H = ∫ρ c_p dT + ρ L f(T)
```
상변화에서 잠열 L 흡수·방출. 기계공학 열전달 표준 방법.

## 단계 전이 메커니즘

MPM에서 입자별로 phase 상태를 보유. 온도 임계값(T_melt) 또는 위치 임계(y < ground) 도달 시 구성방정식을 액체 모델 → 고체 모델로 교체. **두 솔버 갈아끼우는 게 아닌 한 솔버 안 동적 스왑**.

## MPM 구현체

- **1순위**: Taichi 기반 MPM — Python, MIT 라이선스, 공식 예제(jelly·snow·sand) 풍부
- **보조**: SPlisHSPlasH (순수 액체), EmberGen (연기)

## 솔버 선택 자동화 (LLM ② 책임)

- 액체·점성 흐름 → SPH 또는 MPM
- 변형·파괴 → MPM
- 입자성 (모래·먼지) → MPM 또는 DEM
- 기체·연기 → Eulerian (격자 기반)

## 관련 Wiki 페이지

- [[llm-separation-design]] — LLM ②가 이 구성방정식을 선택
- [[mythrill-architecture]] — 전체 아키텍처 내 MPM 솔버 위치
- [[pre-bake-vfx-workflow]] — 시뮬레이션 결과가 베이크되는 워크플로우
- [[mythrill-pipeline]] — 시스템 핵심 차별점으로서의 물리 정합성

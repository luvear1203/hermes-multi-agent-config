---
title: "LLM 분리 설계"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - llm
  - architecture
  - design-pattern
  - ai
sources:
  - "~/.hermes/wiki/raw/obsidian-vault/Brain/Mythrill_파이프라인/00_시스템코어/아키텍처_v1_0.md"
confidence: high
---

# LLM 분리 설계

Mythrill 파이프라인은 LLM을 단일 호출로 처리하지 않고 의도적으로 **두 단계로 분리**한다.

## 분리의 이유

| 이유 | 설명 |
|------|------|
| 능력 차원 차이 | 의도→물질 매칭(LLM ①)과 솔버→파라미터 결정(LLM ②)은 다른 추론 능력 요구 |
| 독립 검증 | 각 단계의 정확도를 분리해서 측정·개선 가능 |
| 모델 교체 유연성 | LLM ②만 더 나은 모델로 교체 가능 |
| 비용 최적화 | LLM ①은 고성능 모델, LLM ②는 오픈소스 모델 등 차등 적용 |
| 사용자 개입 지점 | LLM ① 후 사용자 확인으로 잘못된 매칭 조기 차단 |

## LLM ① 책임

- 자연어 의도 파싱
- 거동 단계 분리 (예: 흘러내림 → 응고 2단계)
- 단계별 현실 물질 후보 선정
- 시각 의도 키워드 추출 (색·발광 등)

## LLM ② 책임

- 단계별 적합 솔버 선택 (SPH / MPM / DEM / Eulerian)
- 솔버별 SI 단위 물리 파라미터 결정
- 단계 전이 조건 명시 (예: y < threshold)

## 단일 호출로 통합하지 않는 근거

검증된 가정: 단일 호출로 두 단계를 동시 처리하면 출력 품질이 저하된다.

- 한 번에 너무 많은 결정 → 모델 일관성 저하
- 사용자 개입 지점 상실 → 잘못된 물질 매칭이 시뮬까지 진행
- 모델 교체 시 전체 영향 → 점진 개선 어려움

이 가정은 2차 스파이크([[mythrill-spike-02]])에서 검증 예정.

## 구성방정식 라이브러리 (LLM ②가 매핑)

### Carreau-Yasuda 모델 (비뉴턴 유체)
```
η(γ̇) = η_∞ + (η_0 - η_∞) · [1 + (λγ̇)^a]^((n-1)/a)
```
- n<1: 전단박화 (페인트·케첩), n>1: 전단증화 (옥수수전분)
- 판타지 매핑: "빠르게 휘두를수록 단단해지는 검기" → n>1

### Arrhenius 식 (온도 의존 점성)
```
μ(T) = μ_0 · exp(E_a / RT)
```
- 저온에서 점성 폭증 → 촛농의 응고 거동

### Enthalpy 방법 (상전이)
```
H = ∫ρ c_p dT + ρ L f(T)
```
- 상변화에서 잠열 L 흡수·방출

## 관련 Wiki 페이지

- [[mythrill-architecture]] — 전체 시스템 아키텍처
- [[three-branch-regression]] — LLM ①/② 이후의 사용자 확인 분기
- [[mpm-constitutive-equation-swap]] — LLM ②가 선택하는 MPM 구성방정식
- [[mythrill-spike-01]] — 1차 검증에서 입증된 LLM 구조화 출력 신뢰성
- [[llm1-validation]] — LLM ① v3 동결
- [[mythrill-spike-02]] — LLM ② 2차 스파이크 (단일 호출 vs 분리 가정 검증)

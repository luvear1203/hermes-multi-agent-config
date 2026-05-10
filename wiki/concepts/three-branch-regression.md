---
title: "3분기 회귀"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - architecture
  - ux
  - optimization
  - regression
sources:
  - "~/.hermes/wiki/raw/obsidian-vault/Brain/Mythrill_파이프라인/00_시스템코어/아키텍처_v1_0.md"
confidence: high
---

# 3분기 회귀 (Three-Branch Regression)

Mythrill 파이프라인의 핵심 차별점 중 하나. 사용자 확인 ② 단계에서 수정 의도에 따라 가장 저렴한 경로로 회귀시켜 비용을 최소화하는 설계.

## 분기 정의

| 분기 | 사용자 판단 | 회귀 대상 | 비용 |
|------|------------|-----------|------|
| Yes | 결과 확정 | (베이킹으로 진행) | — |
| No-A | 물질 매칭 자체가 잘못됨 | LLM ① 재실행 | 가장 비쌈 |
| No-B | 물질은 맞지만 거동 어색 | LLM ② 재실행 (시뮬 다시) | 중간 |
| No-C | 물리는 맞지만 색·시각만 어색 | 시각 오버레이 재실행 | 가장 저렴 |

## 가치

시뮬레이션이 가장 비싼 단계(수 분~수 시간). 수정 의도에 따라 No-C(시뮬 재사용, 시각만 재실행)로 회귀하면 수십 초 안에 수정 완료.

**기존 도구(Niagara, VFX Graph, Houdini)와의 차이**: 어느 부분을 수정하든 사실상 처음부터 다시 처리해야 함. 본 시스템은 **수정 의도에 적응적인 회귀 경로**를 제공.

## 사용자 인터페이스 시사점

사용자 확인 ②의 UI는 단순 Yes/No가 아닌 **수정 의도 분류 입력**이 필요:

- 라디오 버튼: "물질 자체를 바꾸고 싶다 / 거동의 강약을 조정하고 싶다 / 색·시각만 바꾸고 싶다"
- 자연어 추가 입력: 사용자의 수정 의도를 LLM이 분류

## 관련 Wiki 페이지

- [[mythrill-architecture]] — 전체 아키텍처에서 3분기 회귀의 위치
- [[llm-separation-design]] — LLM ①/② 분리가 3분기 회귀를 가능하게 하는 설계
- [[pre-bake-vfx-workflow]] — 오프라인 베이크 구조에서 3분기 회귀의 의의
- [[mythrill-pipeline]] — 시스템 차별점으로서의 3분기 회귀

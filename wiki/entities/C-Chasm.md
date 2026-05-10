---
title: C-Chasm
created: 2026-05-03
updated: 2026-05-06
type: entity
tags:
  - c-chasm
  - directory
  - game-ip
  - cosmic-horror
  - mythic-rpg
  - multi-title
sources:
  - ~/.hermes/wiki/raw/obsidian-vault/Brain/C-Chasm/_INDEX.md
  - ~/.hermes/wiki/raw/obsidian-vault/Brain/C-Chasm/00_IP코어/IP코어_v1_2.md
confidence: high
---

# C-Chasm

> **우주 설정은 [[c-chasm-ip-core]] 참조.** 본 페이지는 관련 문서 디렉토리(진입점)입니다.

## 개요

C-Chasm은 **코스믹 호러**를 기반으로 하는 게임 IP 프로젝트다. 한 줄 정의는 "인간의 인식은 얄팍하다. 진실은 인간의 것이 아니다." 이며, 모든 설정이 이 문장에서 파생된다. 우주 본질 (표층/심층 이중 레이어, 매크로 팩션, 신의 세 유형, 두 축, 시간선, 5장 법칙) 은 [[c-chasm-ip-core]] Part 1~5 에 정본화되어 있다.

## 작품 구성

| 작품 | 시간선 | 엔진 | 장르 | 출시 순서 |
|------|--------|------|------|-----------|
| [[C-Chasm_Alpha]] (2D 프리퀄) | 선사시대 | Unity 2D | 트윈스틱 액션 | 1순위 |
| [[본편_RPG_(C-Chasm)]] | 현대 | UE5 + C++ | 3인칭 신화 RPG | 2순위 |

두 작품은 기본적으로 **이스터에그 수준**으로 연결되며 각각 독립 플레이가 가능하다. 단 숨겨진 조건 하 서사축 연결이 발생할 수 있다 ([[c-chasm-ip-core]] Part 4-3 참조).

## 핵심 설계 원칙 (요약)

1. **단일 진실 소스**: 모든 설정은 [[c-chasm-ip-core]] 를 최상위 제약으로 삼는다.
2. **[[cosmic-horror-design-pattern]]**: 심층 진실은 어떤 캐릭터도 명시적 언어로 표현하지 못한다.
3. **[[three-deity-types]]**: 하위 신화 개별 신격은 강림형·회귀형·광기형 중 하나로 분류된다.
4. **비카타르시스 결말**: 어떤 엔딩도 카타르시스적 승리를 제공하지 않는다.

세부 규범은 [[c-chasm-ip-core]] Part 5 (5장 법칙) 참조.

## 폴더 구조

```
C-Chasm/
├── 00_IP코어/          ← 모든 작품의 상위 제약
├── 10_본편RPG_현대3D/  ← 본편 작품 문서군
├── 20_2D프리퀄_선사시대2D/ ← 2D 프리퀄 문서군
└── 99_archive/         ← 폐기·구버전 문서 보존
```

## 현재 상태

- IP 코어: v1.2까지 확정 (매크로 팩션 구조, 하위 신화 독립 원칙, 이중 엔딩 분기 반영)
- 2D 프리퀄: [[C-Chasm_Alpha]] 문서 구조만 확정, 세부 미착수
- 본편 RPG: [[본편_RPG_(C-Chasm)]] 작품정체성 확정, 세부 미착수
- 과거 v7.0(크툴루 침식), v8.0(신앙 소멸) 설계는 archive로 보존

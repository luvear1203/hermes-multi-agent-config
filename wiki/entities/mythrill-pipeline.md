---
title: "Mythrill 파이프라인"
created: 2026-05-03
updated: 2026-05-03
type: entity
tags:
  - mythrill
  - vfx
  - game-tool
  - bake-pipeline
  - indie-game
sources:
  - "~/.hermes/wiki/raw/obsidian-vault/Brain/Mythrill_파이프라인/00_시스템코어/시스템정의_v1_0.md"
  - "~/.hermes/wiki/raw/obsidian-vault/Brain/Mythrill_파이프라인/_INDEX.md"
confidence: high
---

# Mythrill 파이프라인

## 한 줄 정의

전문 VFX 인력 없이 인디·중소 게임사가 고품질 이펙트를 만들 수 있도록, 자연어 의도를 실제 물질의 물리 거동에 매칭해 자동 시뮬레이션·베이크하는 게임 엔진용 에셋 생성 시스템.

## 개요

Mythrill 파이프라인은 인디·소규모 게임 스튜디오(1~10인 규모)를 위한 사전 베이크 방식의 VFX 에셋 생성 파이프라인이다. 디자이너가 자연어로 의도를 입력하면 LLM이 물리적으로 타당한 시뮬레이션 파라미터로 변환하고, 오프라인 시뮬레이션 후 VAT/Flipbook 등의 베이크 에셋을 출력한다.

## 핵심 정체성

- **코드네임**: Mythrill 파이프라인
- **본질**: 사전 베이크 방식의 VFX 에셋 생성 파이프라인
- **입력**: 자연어로 표현된 VFX 의도
- **출력**: 게임 엔진 호환 베이크 에셋 파일 (VAT, Flipbook 등)
- **기반 기술**: LLM 기반 의도 해석 + 물리 시뮬레이션 솔버 (SPH, MPM)
- **정체성 차별점**: 디자이너 직관이 아닌 실제 물질의 물리 거동에 기반

## 핵심 차별점 (세 요소의 교집합)

1. **기계공학 기반 물리 정합성** — 현실 물질의 실제 물리 거동 매칭
2. **자연어 인터페이스** — 수십 개 파라미터 대신 문장으로 입력
3. **베이크 워크플로우** — 오프라인 시뮬레이션 후 저사양 런타임 재생

## 타깃 사용자

- 1차: 인디·소규모 게임 스튜디오 (1~10인)
- 2차: VFX 전담 인력 없는 개발팀, 저사양 PC 타깃 게임 개발자
- 비-타깃: AAA 스튜디오 (자체 파이프라인 보유)

## 현재 상태

- **단계**: 공모전(루키 2026) 출품 준비 중
- **검증**: 1차 스파이크(자연어→VFX 파라미터) 30회 통과 + LLM ① 50입력 검증 91.3% → **v3 동결** ([[llm1-validation]])
- **다음**: [[mythrill-spike-02|2차 스파이크]] (LLM ② SI 단위 매핑) — 2026-05-09 즉시 착수
- **MVP 스코프**: Taichi MPM + 물질 5~10종 + Flipbook 베이크 + 언리얼 5 플러그인 ([[mythrill-mvp-scope]])
- **진짜 마감**: **2026-12-31 EOY MVP 완성**. 공모전 결과는 일정 변동 사유 아님.
- **공모전 마감**: 2026-05-08 신청서 제출 (도전제안서 수정본 1.1~4.2 본문 작성 완료).

## 관련 Wiki 페이지

- [[mythrill-architecture]] — 시스템 아키텍처 상세
- [[mythrill-mvp-scope]] — MVP 스코프 (도전제안서 2.1·3.1·3.2)
- [[pre-bake-vfx-workflow]] — 사전 베이크 워크플로우 개념
- [[ai-rookie-2026]] — 루키 대회 출품 상세
- [[mythrill-spike-01]] — 1차 검증 결과
- [[mythrill-spike-02]] — 2차 스파이크 (LLM ②, 5/9 즉시 착수)
- [[llm1-validation]] — LLM ① 50입력 확장 검증·동결 결정
- [[mythrill-rpg-showcase]] — RPG Living Showcase
- [[natural-language-vfx-pipeline]] — 자연어 VFX 파이프라인 개념
- [[naked-viewer]] — 사용자 확인 ② UI

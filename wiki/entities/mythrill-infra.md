---
title: "Mythrill 인프라 구성"
created: 2026-05-03
updated: 2026-05-03
type: entity
tags:
  - mythrill
  - hardware
  - business
  - infrastructure
sources:
  - "~/.hermes/wiki/raw/obsidian-vault/Brain/Mythrill_파이프라인/30_사업화/장비_사무실_사업자_v1_0.md"
confidence: high
---

# Mythrill 인프라 구성

Mythrill 파이프라인 개발 및 사업화를 위한 장비·사무실·사업자 구성 계획.

## 현재 장비

- **MacBook Air M1** — 현재 사용 중인 유일한 개발 장비

## 예정 장비 (계획)

### 사무실

| 항목 | 결정 |
|------|------|
| 위치 | 학교 옆 (인천대) |
| 형태 | 1인실 |
| 비용 | 월 20만 원 |
| 결정 사유 | 1400W 장비 열 관리 / 24시간 운영 / 학교 인접 |
| 계약 시점 | 장비 구매와 동기화 (미정) |

## 메인 게임 개발 워크스테이션

| 부품 | 사양 |
|------|------|
| GPU | RTX 5090 (수냉 쿨링) |
| CPU | AMD Ryzen 9 9950X3D (수냉 쿨링) |
| RAM | 96GB |
| 저장장치 | SSD 4TB |

## 로컬 AI 보조 장비

| 부품 | 사양 |
|------|------|
| 본체 | Mac Studio 또는 Mac Mini |
| 통합 메모리 | 128GB |

- MLX 프레임워크로 70B~120B급 오픈모델 추론 (Gemma 3, Qwen 72B, Kimi 등)
- 학습/파인튜닝은 클라우드(RunPod, Vast.ai)로. Mac은 추론 전용
- 총 예산 약 1500~1800만 원 추정

## 사업자등록

| 항목 | 결정 |
|------|------|
| 등록 시점 | 컴퓨터 맞춘 후 |
| 형태 | 미정 (간이과세자 vs 일반과세자 세무사 확인 필요) |
| 목적 | API 비용 페이백, 경비 처리 |

### 등록 전 체크리스트
- 세무사 상담 (해외 SaaS 경비 처리 가능 여부)
- 부모 직장가입 여부 확인 (피부양자 영향)
- 학생 창업 지원금 사전 신청 가능한 것 조사
- 간이과세자 vs 일반과세자 결정

## 관련 Wiki 페이지

- [[mythrill-pipeline]] — Mythrill 전체 프로젝트
- [[mythrill-roadmap]] — 장기 로드맵과 인프라 연계

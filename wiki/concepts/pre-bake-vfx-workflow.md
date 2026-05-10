---
title: "사전 베이크 VFX 워크플로우"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - vfx
  - bake
  - workflow
  - offline-simulation
sources:
  - "~/.hermes/wiki/raw/obsidian-vault/Brain/Mythrill_파이프라인/00_시스템코어/시스템정의_v1_0.md"
  - "~/.hermes/wiki/raw/obsidian-vault/Brain/Mythrill_파이프라인/00_시스템코어/아키텍처_v1_0.md"
confidence: high
---

# 사전 베이크 VFX 워크플로우

게임 런타임이 아닌 **디자이너 작업 시점**에서 시뮬레이션을 1회 실행하고, 결과를 텍스처/캐시로 베이크하여 게임에 탑재하는 워크플로우.

## 핵심 원리

1. **오프라인 시뮬레이션**: 디자이너 작업 환경에서 물리 시뮬레이션 실행 (수 분~수 시간)
2. **베이킹**: 시뮬 결과를 VAT/Flipbook 등 정적 텍스처로 변환
3. **저비용 런타임 재생**: 게임 실행 중에는 텍스처 샘플링만 → GPU 부하 최소화

## Mythrill v0.0 vs v1.0

| 항목 | v0.0 (폐기) | v1.0 (현재) |
|------|-------------|-------------|
| 시뮬 시점 | 게임 런타임 | 디자이너 작업 시점 |
| LLM 역할 | 런타임 Niagara 파라미터 생성 | 오프라인 솔버·파라미터 결정 |
| 출력 형태 | 파라미터 세트 | 베이크 텍스처/캐시 |
| GPU 부하 | 런타임 시뮬 비용 발생 | 텍스처 샘플링만 (거의 0) |

**v0.0 폐기 사유**: 인디의 핵심 페인포인트가 "런타임 GPU 부하"임을 1차 검증 후 재인식.

## 베이크 기법별 특성

### Flipbook (스프라이트 시트)
- 가장 가벼움 (모바일 가능)
- 2D 빌보드로 카메라 각도 한계
- 거의 모든 게임 VFX의 표준

### VAT (Vertex Animation Texture)
- GPU에서 텍스처 샘플링만으로 재생
- 정점 위치·노멀을 픽셀 단위 인코딩
- 토폴로지 변화는 Soft VAT/Fluid VAT 변종 필요

### Niagara Particle Cache
- 언리얼 네이티브, 임포트 즉시 사용
- 입자 단위 정보 유지 → 추가 효과 용이
- 입자 수 × 프레임 수로 용량 큼

## 장점

- **저사양 호환**: 인디 게임의 타깃 사용자(중저사양 PC) 환경에서 60fps 유지
- **비용 효율**: 1회 시뮬레이션 후 런타임 시뮬 비용 0
- **Houdini 대체 가능성**: 고가 도구 없이 동등한 워크플로우 접근

## 관련 Wiki 페이지

- [[mythrill-architecture]] — 베이크 단계의 아키텍처 내 위치
- [[three-branch-regression]] — 베이크 전 수정 회귀 경로
- [[mythrill-pipeline]] — Mythrill의 핵심 가치 제안으로서의 베이크
- [[natural-language-vfx-pipeline]] — 베이크 워크플로우와 자연어 인터페이스의 결합

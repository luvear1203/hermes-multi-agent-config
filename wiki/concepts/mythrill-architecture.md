---
title: "Mythrill 시스템 아키텍처"
created: 2026-05-03
updated: 2026-05-03
type: concept
tags:
  - mythrill
  - architecture
  - pipeline
  - llm
  - simulation
  - bake
sources:
  - "~/.hermes/wiki/raw/obsidian-vault/Brain/Mythrill_파이프라인/00_시스템코어/아키텍처_v1_0.md"
confidence: high
---

# Mythrill 시스템 아키텍처

Mythrill 파이프라인의 처리 흐름과 구조 정의. 시스템의 "어떻게"를 담당한다.

## 9단계 처리 흐름

| 단계 | 이름 | 입력 | 출력 | 분류 |
|------|------|------|------|------|
| 1 | 자연어 입력 | 디자이너 의도 텍스트 | — | 입력 |
| 2 | LLM ① 의도 파싱·물질 매칭 | 자연어 의도 | 단계 분리·물질 후보 | LLM 처리 |
| 3 | 사용자 확인 ① | LLM ① 출력 | Yes / No | 사용자 확인 |
| 4 | LLM ② 솔버·파라미터 결정 | 확정된 물질 매칭 | 솔버 종류·SI 단위 파라미터 | LLM 처리 |
| 5 | 시뮬레이션 실행 | 솔버·파라미터 | 입자 거동 시계열 | 시뮬레이션 |
| 6 | 시각 오버레이 | 시뮬 결과 + 시각 의도 | 색·발광 적용 결과 | 시각화 |
| 7 | 사용자 확인 ② | 최종 시각 결과 | Yes / No-A / No-B / No-C | 사용자 확인 |
| 8 | 베이킹 | 확정된 결과 | VAT/Flipbook 파일 | 출력 |
| 9 | 에셋 파일 출력 | 베이크 파일 | 게임 엔진 임포트용 에셋 | 출력 |

## 데이터 흐름

```
[자연어 텍스트]
    ↓ (LLM ①)
[JSON: 단계 분리 + 물질 후보]
    ↓ (사용자 확인 ① Yes)
[JSON: 확정된 물질 매칭]
    ↓ (LLM ②)
[JSON: 솔버 + SI 단위 파라미터]
    ↓ (시뮬레이터)
[입자 시계열 데이터: 위치·속도·밀도 배열]
    ↓ (시각 오버레이)
[입자 데이터 + 색상·발광·투명도 적용 결과]
    ↓ (사용자 확인 ② Yes)
[베이커 입력]
    ↓
[VAT/Flipbook 텍스처 파일]
```

## 시스템 경계

- **내부**: 1~9단계 전체 (에셋 파일 출력까지)
- **외부**: 게임 엔진 임포트, 액터·이벤트 연결, 런타임 재생 트리거, 라이팅·포스트프로세싱 합성

## MPM 단일 솔버 + 동적 구성방정식 스왑

다중 솔버를 stitch하지 않고, MPM 단일 솔버 위에서 입자별로 구성방정식을 동적으로 교체. Carreau-Yasuda, Arrhenius, Enthalpy 방법으로 비뉴턴 유체·온도 의존 점성·상전이를 한 솔버 안에서 처리.

### 메인 구현체
- **1순위**: Taichi 기반 MPM (Python, MIT 라이선스)
- **보조**: SPlisHSPlasH (순수 액체), EmberGen (연기)

## 베이크 우선순위

| 순위 | 기법 | 용도 |
|------|------|------|
| 1 | Flipbook | 2D 빌보드 (검기·마법·연기 90%) |
| 2 | VAT | 3D 메시 변형 |
| 3 | Niagara Cache | 입자성 강조 |
| 4 | Volume Texture/VDB | 고사양 한정 |
| 5 | Geometry Cache | 시네마틱 일회성 |
| 6 | Heightmap/Flow Map | 표면 효과 |

## 확장 가능성

- 솔버 라이브러리 100+ 물질로 확장
- LLM ①/②에 다른 모델 할당
- 출력 포맷: Geometry Cache, Niagara Cache, USD 등 추가
- 게임 엔진: 언리얼(1순위) → 유니티(Phase 2)

## 관련 Wiki 페이지

- [[mythrill-pipeline]] — 시스템 정의 ("무엇")
- [[llm-separation-design]] — LLM 두 단계 분리 설계 상세
- [[three-branch-regression]] — 사용자 확인 ②의 3분기 회귀
- [[mpm-constitutive-equation-swap]] — MPM 구성방정식 스왑 상세
- [[pre-bake-vfx-workflow]] — 베이크 워크플로우 개념

# Hermes Multi-Agent Configuration

> Claude + DeepSeek Pro + Gemini Pro → Gemma 4 멀티 에이전트 오케스트레이션 시스템

## 아키텍처

```
사용자 (아이디어/계획)
        │
┌───────▼──────────┐
│  Orchestrator     │  DeepSeek Pro V4
│  • 계획 검토/수정   │  • 역할 분배
│  • 최종 승인       │  • 결과 취합
└──┬──────┬──────┬──┘
   │      │      │
┌──▼──┐ ┌▼───┐ ┌▼──────┐
│Researcher│ │Analyst│ │Dev-Gemma│
│Claude    │ │Gemini │ │Gemma 4  │
│논문 검색  │ │중복확인│ │코드 구현 │
└─────────┘ └──────┘ └─────────┘
        │
   ┌────▼─────┐
   │ Cron Job  │  API 사용량 체크
   └────┬─────┘
   ┌────▼─────┐
   │ Discord   │  결제 확인 DM
   └──────────┘
```

## 프로필 구성

| 프로필 | 모델 | 역할 |
|--------|------|------|
| `orchestrator` | DeepSeek Pro V4 | 계획 검토, 역할 분배, 결과 취합 |
| `researcher` | Claude Sonnet 4 | 논문 검색, 지식 수집, 선행연구 조사 |
| `dev-gemma` | Gemma 4 (로컬 Ollama) | 코드 구현, TDD 개발 |

## 빠른 시작

### 1. Hermes Agent 설치

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### 2. 설정 복원

```bash
git clone https://github.com/luvear1203/hermes-multi-agent-config.git
cd hermes-multi-agent-config
bash restore.sh
```

### 3. API 키 설정

```bash
orchestrator setup     # DeepSeek API 키
researcher setup        # Anthropic API 키
```

### 4. Gemma 4 로컬 서버 (나중에)

```bash
ollama pull gemma4
ollama serve
# dev-gemma 프로필이 http://localhost:11434/v1 로 연결됨
```

### 5. Discord Gateway (나중에)

```bash
orchestrator gateway setup   # Discord 봇 토큰 입력
orchestrator gateway install
orchestrator gateway start
```

## 사용법

### Orchestrator 실행

```bash
orchestrator
# 또는
hermes -p orchestrator
```

### 아이디어 검증 파이프라인

```
# Orchestrator에게 아이디어 던지기
"AI 기반 실시간 코드 리뷰 도구를 만들고 싶어. 검증해줘."
→ Researcher가 논문 검색
→ 결과 취합 후 보고
→ 개발 가능하면 Dev-Gemma에게 위임
```

### 설정 변경사항 저장

```bash
# Hermes 설정을 수정한 후
cd ~/hermes-multi-agent-config
bash sync.sh
git add -A && git commit -m "설정 업데이트"
git push
```

## 디렉토리 구조

```
hermes-multi-agent-config/
├── README.md              # 이 파일
├── .gitignore             # Git 제외 규칙
├── sync.sh                # Hermes → 여기로 동기화
├── restore.sh             # 여기 → Hermes로 복원
├── profiles/
│   ├── orchestrator/
│   │   ├── config.yaml    # DeepSeek Pro 설정
│   │   └── SOUL.md        # Orchestrator 페르소나
│   ├── researcher/
│   │   ├── config.yaml    # Claude Sonnet 설정
│   │   └── SOUL.md        # Researcher 페르소나
│   └── dev-gemma/
│       ├── config.yaml    # Gemma 4 로컬 설정
│       └── SOUL.md        # Developer 페르소나
├── skills/                # 커스텀 스킬
├── cron/                  # Cron 작업 설정
└── scripts/               # 유틸리티 스크립트
```

## 할 일

- [ ] Discord 봇 토큰 발급 및 Gateway 설정
- [ ] Anthropic API 키 발급 (researcher)
- [ ] Google Gemini API 키 발급 (analyst)
- [ ] Gemma 4 출시 후 Ollama 연동
- [ ] API 사용량 모니터링 Cron job 설정
- [ ] 아이디어 검증 파이프라인 스킬 작성

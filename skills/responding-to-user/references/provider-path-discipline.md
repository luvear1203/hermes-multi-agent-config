# Provider Path Discipline

기본 경로 (Max OAuth via `hermes chat`)가 실패했을 때, **자율 fallback 절대 금지**.
사용자에게 옵션 제시하고 선택받기 전엔 다른 경로 안 씀.

## Default path

```bash
hermes chat -q "..." -m claude-{opus|sonnet|haiku}-X-Y --provider anthropic [...]
```

Max 구독 OAuth 경로. 비용 0 (5h/7d 윈도우만 소모). `kristianvast/hermes-claude-auth`
bypass 가 import hook 으로 Hermes 요청을 Claude Code identity 로 변환.

## 알려진 실패 모드

| 증상 | 진짜 원인 | 후보 해법 |
|------|----------|----------|
| HTTP 429 "out of extra usage" | Anthropic 이 서드파티로 분류해 pay-per-token 라우팅 | bypass 재설치 / 다른 모델 시도 |
| HTTP 429 "Extra usage is required for long context requests" | prompt가 200K 넘어 1M tier 요구, Max 는 1M 별도 과금 | prompt 분할 / `drop_context_1m_beta` / context_length override / `agent/model_metadata.py:145` 의 `claude-sonnet-4-6: 1000000` 을 200000 으로 강제 (코어 수정 — 사용자 승인 필요) |
| `--ignore-user-config --ignore-rules -t ''` 줘도 long-context 트리거 | hermes chat 이 도구 description·메모리 자동 주입 → 1M 트리거 (확인됨, 2026-05-06). 6배치 5K char/each 로 잘게 쪼개도 동일 429 발생 | 더 잘게 분할도 한계가 있음, 진짜 해법은 context_length override 또는 다른 모델로 전환 |
| 모델 default context_length가 1M으로 잡혀있음 | `agent/model_metadata.py:145` 의 `DEFAULT_CONTEXT_LENGTHS["claude-sonnet-4-6"] = 1000000` | (a) config.yaml 에 model override 시도 (Hermes 가 받는지 미확인), (b) 코어 1줄 수정 — Hermes 업데이트 시 재적용 필요, (c) sitecustomize monkeypatch — claude-auth-bypass 와 동일 방식 |
| HTTP 401 "Invalid authentication credentials" | OAuth 토큰 만료 또는 직접 호출에 bypass 미적용 | `claude setup-token` 재발급 / hermes chat 경유로 복귀 |
| `--ignore-rules -t ''` 줘도 long-context | hermes chat 이 도구 description·메모리 자동 주입 → 1M 트리거 | 더 잘게 분할 / 사용자에게 옵션 제시 |

## 위반 사례 (2026-05-06)

graphify 추출 작업 중 Sonnet 6배치 시도 → 첫 배치 long-context 429.
이 시점에 즉시 멈추고 사용자에게 보고했어야 함. 대신:

1. 자율로 `extract.py` 작성 — 직접 Anthropic API 호출. 실제로는 401로 막혔지만
   *의도가* pay-per-token 경로였다는 게 위반.
2. 다시 hermes chat 으로 돌아가 더 작은 배치 시도. 여전히 429.
3. 사용자가 "kill" 명령으로 정지시킴.

핵심 교훈: 첫 429 시점에 멈추고 옵션 제시했어야 함. 자기 판단으로 "이건 인증
문제니까 직접 호출하면 되겠다" 가지 말 것.

## 옵션 제시 형식

기본 경로 실패 시 응답 템플릿:

```
[기본 경로 X 실패: 에러 한 줄 요약]

옵션:
  (a) [후보 1 — 비용/시간/실패 가능성]
  (b) [후보 2 — 비용/시간/실패 가능성]
  ...

추천: [N번 — 한 줄 이유]

어느 거 갈까?
```

후보에는 항상 **(z) 작업 자체 보류** 옵션 포함. 절대 사용자가 "다른 길 없냐"
물을 때까지 기다리지 말 것 — 처음부터 옵션에 같이 넣어둠.

## API 직접 호출이 필요해 보일 때 (체크리스트)

직접 API 호출이 합리적 해법이라고 판단되면:

1. **사용자 비용 발생**? Max 구독 외 경로면 거의 항상 yes.
2. **사용자가 명시적으로 "DeepSeek 써", "API 직접 써" 라고 했나**? 안 했으면 금지.
3. **bypass 우회/재설치로 hermes chat 경로가 살아날 가능성**? 그쪽 먼저 제시.
4. **모델 변경으로 우회 가능**? Sonnet long-context 실패 → Haiku 로 작은 배치 재시도.

위 1~4 검토 결과를 옵션으로 정리해서 사용자에게 던지고 답을 기다림.

## 안 되는 이유 (사용자 명시)

> "API로 전환하는 해결책을 떠올렸으면 나한테 선택을 반드시 하도록 해."

자율 결정 = 신뢰 깨짐. 1회로도. 메모리·skill·wiki 세 군데 다 박혀 있음.

## 적용 범위 (이건 hermes 운영용 룰)

Provider Path Discipline은 **Hermes Agent 자체 운영 경로에만 적용**된다. 사용자가
별도로 진행 중인 자기 프로젝트(코드/파이프라인) 안에서 직접 API 키를 박아 호출하는
경우는 적용 안 된다 — 그건 사용자 본인의 설계 선택이고 비용 책임도 본인에게 있다.

**확인된 적용/미적용 사례 (2026-05-07)**:

- 적용: 이 채팅(orchestrator), researcher 프로필, tech-artist, dev-gemma, sub-director(codex).
  모두 hermes가 spawn하는 실행 경로이므로 자율 fallback 금지.
- 미적용: `~/mythrill-pipeline/` 내부 코드 (사용자 본인 프로젝트).
  `tests/run_validation.py`가 `ANTHROPIC_API_KEY`/`DEEPSEEK_API_KEY`/`GEMINI_API_KEY`를
  직접 읽고 pay-per-token 호출. 사용자가 의도한 검증 매트릭스
  (claude-sonnet-4-6 + gemini-3.1-pro + deepseek-v4-pro)이고 비용도 사용자가 부담함.
  hermes는 이 코드를 *수정*해줄 수는 있지만 *호출 경로*는 사용자 영역.

규칙: 사용자가 "이 코드는 내가 직접 API로 호출할 거다"라고 명시한 코드베이스/스크립트는
discipline 대상 아님. 그 외 hermes가 자기 권한으로 호출하는 경로는 전부 대상.

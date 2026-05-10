---
title: Model Prompting Conventions — optimal prompt format per model version
created: 2026-05-04
updated: 2026-05-10
type: architecture
tags: [multi-agent, prompt, model]
sources:
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags
  - https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide
  - https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide
  - https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide
  - https://developers.openai.com/api/docs/guides/prompt-guidance
  - https://www.anthropic.com/news/claude-haiku-4-5
confidence: high
---

# Model Prompting Conventions

Optimal prompt format differs per model. Source-Enforcement: every section below cites the official guide it draws from. When reinforced versions ship, fetch the new official guide and update this page first; harness prompts (delegate_task, hermes chat --profile X, Sub-Director review) MUST branch by model.

**페이지 수정 이력 주의**: 2026-05-10 사용자 정정으로 외부 1차 소스 직접 페치(WebFetch) 후 전면 재작성. 이전 버전은 model 일반 지식 기반 추정이었음.

## Claude Opus 4.7 (Director, default `hermes chat`)

Source: [Anthropic Prompting best practices — Prompting Claude Opus 4.7 section](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) (fetched 2026-05-10)

**Format**: XML tags (`<task>`, `<context>`, `<instructions>`, `<examples>`, `<document>`, `<frontend_aesthetics>` 등 — Claude는 XML 태그를 의미 구분자로 학습됨).

**Effort levels (Opus 4.7는 strict하게 respect — 4.6 대비 변화)**:
- `max`: intelligence-demanding 태스크 한정. overthinking 위험.
- `xhigh` (신설): 코딩·agentic 기본 추천.
- `high`: intelligence-sensitive 최소 권장.
- `medium`: cost-sensitive — 복잡 태스크에선 under-thinking 위험.
- `low`: latency-sensitive·short scoped 한정.

**Hermes orchestrator 현재 설정**: `reasoning_effort: medium` ← Anthropic 권장 `high` 이상보다 낮음. 검토 필요.

**핵심 동작 변화 (vs 4.6)**:
- Verbosity: 태스크 복잡도에 따라 자동 calibration. 고정 length 원하면 명시.
- Tool use: 4.6보다 적게 사용 (reasoning 더 함). tool 더 쓰게 하려면 effort↑ + 명시적 prompt.
- Subagent: 적게 spawn. "Spawn multiple subagents in the same turn when fanning out across items" 같이 명시 권장.
- Literal instruction following: scope 명시 안 하면 generalize 안 함. "Apply this formatting to every section, not just the first one" 처럼 scope 명시 필요.
- 톤: 더 direct, validation 적음, emoji 적음.

**Code review 한정 강한 권장 (직접 인용)**:
> "Report every issue you find, including ones you are uncertain about or consider low-severity. Do not filter for importance or confidence at this stage - a separate verification step will do that. Your goal here is coverage..."

**Long context (>20k tokens) 패턴**:
- Long-form data를 prompt **상단**에 배치 (query는 하단). 이것만으로 응답 품질 최대 30% 향상.
- Multi-document: `<documents><document index="n"><source>...</source><document_content>...</document_content></document></documents>`
- Ground in quotes: 답변 전 관련 부분 인용 요청.

**Pitfalls 확인됨**:
- `service_tier: priority`는 Opus 4.7 미지원 (HTTP 400 'speed parameter not supported'). [[multi-agent-system]] 2026-05-10 commit 1cb4c4a 참조.

**Director profile 작성 템플릿 (XML)**:
```xml
<role>
You are <X>. <one-line responsibility>.
</role>

<peers>
- <name1>: <role/model>
- <name2>: <role/model>
</peers>

<context>
<background facts; prior decisions; reference docs/commits>
</context>

<goal>
<single concrete deliverable>
</goal>

<constraints>
- <rule 1>
- <rule 2>
</constraints>

<output_format>
<exact structure: markdown sections, JSON schema, code-only, etc.>
</output_format>

<input>
<the actual data — place LONG inputs above query for >20k tokens>
</input>
```

## Claude Sonnet 4.6 (Researcher A 후보, 실제 운용은 Sonnet 4.5)

Source: 같은 [Anthropic best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — Opus 4.7와 동일 가이드 (Sonnet 4.6 별도 섹션 없음, "covers Claude Opus 4.7, 4.6, Sonnet 4.6, Haiku 4.5" 명시).

XML scaffold 동일. 운용 주의:
- Anthropic Max OAuth에서 long-context (>200K) 시도 시 429 빈발 → researcher profile은 `claude-sonnet-4-5-20250929` 사용 (memory feedback_provider_path_discipline.md 참조).
- 코드 생성 시 명시: "no placeholder, no TODO, no examples".

## Claude Haiku 4.5 (dev-gemma — Code Implementation worker)

Sources:
- [Anthropic best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) (Haiku 4.5 covered)
- [Introducing Claude Haiku 4.5](https://www.anthropic.com/news/claude-haiku-4-5)

**가이드**:
- Sonnet 4 수준 코딩 성능을 1/3 비용·2배 속도로 제공 (Anthropic 공식 발표).
- 권장 패턴: "Sonnet 4.5가 복잡 문제를 multi-step plan으로 쪼개고, 여러 Haiku 4.5를 parallel로 실행"
- XML scaffold 사용 가능. plain markdown도 OK.
- 자연 톤 (paragraph 우선, list/heading/bold/emoji 자제 — Anthropic 추천)
- Output format을 명시적으로 pin (Haiku는 빠르지만 prose 추가 경향)
- System prompt를 ~5k 토큰 이내로 (Haiku는 빠른 만큼 context budget 적음)

**Haiku 4.5 라이트 템플릿 (XML)**:
```xml
<role>You are <X> running on Haiku 4.5.</role>
<task>
<one paragraph: goal + key constraints + expected output>
</task>
<input>
<data>
</input>
Return: <explicit format>.
```

## GPT-5.5 (Sub-Director, Codex OAuth)

Sources (1차 자료, 2026-05-10 fetch 기준):
- [GPT-5 Prompting Guide (cookbook)](https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide)
- [GPT-5.1 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5-1_prompting_guide)
- [GPT-5.2 Prompting Guide](https://cookbook.openai.com/examples/gpt-5/gpt-5-2_prompting_guide)
- [OpenAI GPT-5.5 prompt guidance](https://developers.openai.com/api/docs/guides/prompt-guidance) (released 2026-04-25)

**Format (GPT-5.5 공식 framework)**: 다음 7개 섹션 markdown headings.
- **Role**: 1-2 문장으로 function·context 정의
- **Personality**: 톤·태도·협업 스타일
- **Goal**: user-visible outcome
- **Success criteria**: 마무리 전 충족돼야 할 조건
- **Constraints**: 정책·안전·증거 한계
- **Output**: 섹션·길이·톤 명시
- **Stop rules**: 언제 retry/fallback/abstain

**핵심 원칙 (직접 인용)**:
- "GPT-5.5 is strongest when the prompt defines the target outcome, success criteria, constraints, and available context, then lets the model choose the path." → **outcome-first**
- "Avoid unnecessary absolute rules. Use those words [ALWAYS/NEVER] for true invariants — safety rules, required output fields, or actions that should never happen."
- "minimum evidence sufficient to answer correctly, cite it precisely, then stop"

**GPT-5.2 framework (CTCO)**: Context → Task → Constraints → Output. Reasoning Effort 명시 (Minimal/Low/Medium/High). Scope Discipline로 verbosity drift 방지.

**Reasoning Effort 가이드**:
| Level | 용도 |
|---|---|
| High | 복잡 multi-step. one task per turn 시 peak. |
| Medium | "Many workflows can be accomplished with consistent results at medium" — 기본 |
| Low | speed 중심, 단순 태스크 |
| Minimal | latency-sensitive. 명시적 planning prompt 필요 |

**Hermes sub-director 현재 설정**: `reasoning_effort: xhigh` (config 검사 결과). OpenAI 가이드는 high까지 권장. xhigh는 Anthropic effort 어휘 — Codex가 'high'로 매핑할 가능성 높음. 후속 검증 필요.

**Agentic 패턴**:
- Eagerness↓: effort↓ + 명시 budget ("absolute maximum of 2 tool calls") + escape hatch.
- Autonomy↑: effort↑ + persistence block ("keep going until the user's query is completely resolved" / "Never stop...when you encounter uncertainty—research or deduce the most reasonable approach").
- Tool preamble: "Always begin by rephrasing the user's goal...outline a structured plan detailing each logical step"

**Tool/Function calling**:
- Responses API + `previous_response_id` 사용 시 reasoning 재사용 → "statistically significant improvements" + 비용↓.
- "You should at most make one tool call at a time" (병렬 금지).
- File 편집은 `apply_patch` 권장 (training distribution).

**Anti-patterns (직접 인용)**:
- "Poorly-constructed prompts containing contradictory...instructions can be more damaging to GPT-5"
- 모호한 지시 → 모델이 reasoning token을 reconcile에 낭비
- 과한 thoroughness 강요 → "maximize_context_understanding" 같은 키워드는 "unnecessary tool usage" 유발
- API는 기본 non-markdown 반환. Markdown 원하면 명시.
- 긴 대화에서 formatting rule은 3-5 user message마다 재서술 필요 (stale adherence 방지).

**Sub-Director profile 작성 템플릿 (markdown)**:
```markdown
# Role
<one line: who you are, what model>

# Goal
<one specific verb-led action>

# Success Criteria
- <condition that must be true before finalizing>
- <...>

# Context
<facts, references, commit SHAs, file paths>

# Constraints
- <rule 1>
- <rule 2>

# Output
<exact format spec — markdown sections, JSON schema, fixed checklist>

# Stop Rules
- <when to retry / fallback / abstain>

# Inputs
<data block>
```

JSON 응답 강제 시:
```
Respond ONLY with a JSON object matching this schema:
{ "field": "type|enum|...", ... }
No prose, no markdown fencing.
```

## DeepSeek V4-Pro (Researcher B)

OpenAI-compatible API. GPT-5.5와 동일 markdown headings 양식 적용 (계열 호환). 검증된 1차 소스 (DeepSeek 공식 prompt guide) 미확보 — 다음 사이클에 deepseek.com 공식 docs 페치해서 갱신 필요. **Confidence: low**.

운영상 관찰:
- system prompt에 role · peers · output contract 명시 시 안정성↑
- JSON mode 지원 (response_format)
- Long-context는 Anthropic보다 약함 — ~64K 입력 이상은 chunk

## Gemini 2.x Pro / Gemma 4 31B IT (tech-artist)

검증된 1차 소스 (Google AI Studio 공식 prompt guide) 본 사이클 미확보. **Confidence: low**.

운영상 확인된 제약:
- Hermes 1회 호출 system prompt가 ~25k 토큰 (89개 skill SKILL.md 로드).
- gemma-4-31b의 Tier 1 paid input_tokens_per_minute = 16k hard cap → 1요청에서 한도 초과.
- 워커는 hermes chat 경유 대신 직접 API 호출(thin custom script)이 적합. 자세히 [[multi-agent-system]] 2026-05-10 dev-gemma swap history.

다음 사이클: ai.google.dev/gemini-api/docs 공식 prompting guide 페치 후 갱신.

## Common Recommended Pattern (모든 모델 공통, [Alex AI 영상 인사이트, 검증 출처 미확보])

System prompt 최상단에 다음 3블록:

```
[ROLE] You are <role name>. <one-line responsibility>.
[PEERS] Your peers: <name1>=<role>, <name2>=<role>...
[CONTRACT] Output contract: <markdown / JSON / code / etc.>. <required fields>.
```

## Source-Enforcement Pattern (R&D Engineer A·B 적용)

Claude (XML):
```xml
<source_rule>Every claim requires a source URL/DOI. Discard chunks without sources.</source_rule>
```

GPT-5.5/DeepSeek (markdown):
```markdown
# Source Rule
Every claim requires a source URL/DOI. Discard chunks without sources.
```

## Update Policy

- 모델 reinforced version 출시 시 즉시 공식 가이드 fetch → 본 페이지 갱신 → harness prompt에 반영.
- 갱신 시 기존 운용 prompt도 정합성 점검.
- **1차 소스 우선** (cookbook.openai.com, platform.claude.com, ai.google.dev). 2차 매체 인용은 1차 인용 보조용만.

## Related Docs

- [[roles]] · [[cost-tiers]] · [[validators]] · [[multi-agent-system]] · [[orchestrator-protocol]]

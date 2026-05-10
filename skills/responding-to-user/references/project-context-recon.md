# Project Context Reconnaissance

When the user names an active project (Mythrill, C-Chasm, hermes-config, etc.), do not answer recommendations or evaluations from memory alone. Memory entries are one-line summaries — they go stale and they omit the operational state. Always reconcile against the wiki + filesystem before forming a position.

## Why this exists

Recurring failure mode: user invokes a project, the agent rattles off a plausible answer based on memory + general LLM knowledge, and the user has to correct: "관련 이전 진행사항을 너가 제대로 모르네" / "그건 이미 결정된 거야" / "이전에 그렇게 안 하기로 했잖아". Each correction costs a turn and erodes trust. The fix is procedural, not heroic — read the project's authoritative state first, every time.

Concrete trigger from 2026-05-07: user said "Mythrill 프로젝트 개발 이어서 들어가자" and later asked about adding GPT to the validation matrix. The agent recommended GPT-5.5 / GPT-5.4 without first checking that the matrix was already locked at three models (sonnet-4-6 + gemini-3.1-pro + deepseek-v4-pro) and the user had already removed GPT from the application. User correction: "Mythrill 관련 이전 진행사항을 너가 제대로 모르네." Avoidable with a 30-second wiki + ls pass.

## Recon order

Before producing the substantive answer, run these in order. Stop only when you've covered all relevant axes for the question.

### 1. Wiki entity sweep

```
Search_files(path="~/.hermes/wiki", pattern="<project-name>", output_mode="files_only")
```

Then read the highest-signal hits:

- `~/.hermes/wiki/entities/<project-slug>.md` — top-level project page
- `~/.hermes/wiki/entities/<project-slug>-*.md` — phase / subsystem pages (mvp-scope, roadmap, validation, pipeline, etc.)
- `~/.hermes/wiki/concepts/*<project-keyword>*.md` — concept pages tied to the project
- `~/.hermes/wiki/log.md` — chronological updates; grep for the project name
- `~/.hermes/wiki/architecture/*.md` — if the question touches roles, model assignments, cost tiers, or governance

The wiki is the single source of truth. If a wiki page disagrees with memory, the wiki wins. If the wiki is silent, that itself is a fact — surface it explicitly: "위키엔 X 관련 페이지 없음, 추측하지 않고 사용자 확인 받겠음."

### 1a. MUST-READ slots inside the project entity pages

When you open the entity pages above, do NOT skim. The following five slots are load-bearing and have caused user corrections when missed:

1. **Demo / acceptance set.** Look for a section titled \"시연\", \"demo\", \"검증용 테스트\", \"MVP 검증\", \"acceptance\" or similar. These are the prompts/cases the project must clear at completion. They take priority over any general dataset (e.g. inputs.txt) when designing test/golden sets. Mythrill mvp-scope.md lines 54-66 are the canonical example: 5 prompts that drive every later validation choice.
2. **Locked decisions / matrices.** Model matrices (\"validation matrix fixed: A + B + C\"), library shortlists, frozen schemas, frozen prompt versions. If the user mentions a project and you're about to recommend an addition or substitution to one of these, STOP and verify the matrix is still open.
3. **Excluded paths.** Look for \"제외\", \"금지\", \"미투입\", \"out of scope\", \"never\". E.g. Mythrill mvp-scope.md says GPT explicitly excluded; mythrill-pipeline.md / roadmap says external engines (Houdini, YADE, etc.) excluded for marketing/positioning reasons. Recommending an excluded item = automatic correction.
4. **Differentiation / positioning statement.** \"AI 네이티브\", \"외부 도구 의존 최소화\", \"기존 X 대체\". General-purpose recommendations from outside the project must pass this filter. If your recommendation duplicates the very thing the project is trying to replace, the recommendation is wrong.
5. **Phase boundary.** Where on the roadmap the project currently sits. Phase-2 tooling proposals during a Phase-1 spike are out of phase. Cross-check the current phase against `entities/*-roadmap.md` before proposing anything.

If any of these slots is missing from the wiki page, surface the gap before answering — do not invent a value.

### 2. Filesystem state sweep

For each project that has its own directory, do a quick recon:

```
ls ~/<project-dir>/                        # top-level layout
ls ~/<project-dir>/<active-subdir>/        # the area the user mentioned
head -N <key-config-or-prompt-file>        # first lines of pivotal files
ls ~/<project-dir>/tests/results/ | tail   # most recent validation runs
wc -l <test-input-file>                    # input dataset size
```

Examples for Mythrill:

```
ls ~/mythrill-pipeline/
ls ~/mythrill-pipeline/src/
ls ~/mythrill-pipeline/prompts/
ls ~/mythrill-pipeline/tests/results/ | tail -5
head -80 ~/mythrill-pipeline/tests/run_validation.py
```

Examples for C-Chasm (the wiki page is canonical, but a Brain/ vault may exist):

```
ls ~/Documents/Obsidian\ Vault/Brain/C-Chasm/ 2>/dev/null
```

What you're looking for:

- Empty files (e.g. `prompts/llm2_solver.md` was 0 bytes — that's a key fact)
- Latest dated artifact (most recent CSV, log entry, commit) — anchors "where the project actually is"
- Hardcoded values inside scripts that contradict the question (model IDs, schema fields, dataset size)
- Missing pieces vs. what the wiki promises (gap = next work item)

### 3. Reconcile memory ↔ wiki ↔ disk

Three tiers of truth:

| Tier | What it carries | When it goes stale |
|------|-----------------|---------------------|
| Memory (this skill, `mcp__hermes__Memory`) | One-line summary, "where things stand right now" | Decisions older than ~7 days, or any fact the user changed without an update prompt |
| Wiki (~/.hermes/wiki/) | Authoritative project state, role assignments, validation results | Only when the agent forgets to update it (Immediate-Reflection rule should prevent this) |
| Disk (~/<project-dir>/) | The real code and data | Never — it's the ground truth |

Resolution rule:

- **Disk wins** for "what currently exists / runs / produces output."
- **Wiki wins** for "what was decided / what we're aiming at / who owns what."
- **Memory wins** only as a starting hypothesis to verify against the other two.

If the three disagree, surface the disagreement to the user before acting:

> "메모리엔 X로 적혀 있는데 wiki/<page>는 Y로 명시. 디스크 상태는 Z. 어느 쪽이 현재 결정인지 확인해주세요."

### 4. Then answer

Once recon is done, the answer should:

- Cite specific wiki page(s) and disk path(s) it relied on (one-line provenance, not full quotation).
- Distinguish "verified from disk" vs. "stated in wiki, not yet verified" vs. "guess, please confirm."
- Propose work that fits the project's current phase, not a phase ago. (Mythrill is between Phase 1 spike-01 and spike-02; do not recommend Phase 2-style work.)

## Cost calibration

This recon takes 30-90 seconds and 1-3 tool calls. The penalty for skipping it is at least one wrong recommendation, one user correction, and a turn of remediation — usually more expensive than the recon would have been.

Only skip the recon when:

- The user explicitly says "skip the lookup, just answer X" — and even then, mark the answer as "without recon, may miss recent changes."
- The question is project-agnostic (general programming, environment setup unrelated to the active project).
- You did the recon less than 5 turns ago in the same session and the project state hasn't been touched since.

## Anti-patterns

- **Treating memory as authoritative.** Memory is a hint. Always cross-check.
- **Reading only the wiki and skipping disk.** Wiki may say "MVP target EOY 2026" while disk shows the next-step prompt file is empty. Both facts matter.
- **Reading recon files but answering as if they don't exist.** If you read a file, cite it; if you cite it, your answer must align with what it actually says. Half-recon (read but ignore) is worse than no recon.
- **Bundling recon and the substantive answer in one massive reply.** Run recon silently (or with a one-line "현황 점검 중"), then answer. Do not paste raw `ls` / `head` output unless the user asked for it.

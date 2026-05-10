# Sub-Director → Codex Director Handoff Pattern

When Rule 14 trigger fires (same symptom 2× / external-cause loop / known
signal ignored / cascading-cost decision), the Sub-Director (this Opus chat)
hands the problem to the Director (gpt-5.5 via codex exec). The handoff
prompt is what determines whether you get a useful answer or another guess
cycle.

This file records the prompt-shape that worked in the gemini-3.1-pro-preview
SDK debugging incident (2026-05-07) and a separate plan-review case the same
session, so future handoffs follow the same shape.

## Invocation

```bash
cat > /tmp/handoff.txt <<'EOF'
<prompt body — see sections below>
EOF
codex exec --skip-git-repo-check -m gpt-5.5 "$(cat /tmp/handoff.txt)" 2>&1 | tail -120
```

`--skip-git-repo-check` avoids Codex blocking outside-repo invocations.
`-m gpt-5.5` pins the Director model. `2>&1 | tail -120` keeps the response
visible while clipping Codex's status preamble (which is large).

## Required prompt sections

1. **Role declaration.** First line: "You are the Sub-Director / Director
   reviewing X for project Y. Solve this — do not hand it back." Removes
   ambiguity about whether Codex should ask clarifying questions or commit
   to a recommendation.

2. **Environment.** Project path, venv, active script, recent state
   transitions (e.g. "switched SDK from A to B"). Include enough that
   Codex doesn't have to re-discover it via shell probes.

3. **Current state and observed failure.** Concrete logs, exact error
   strings, what was tried, what each attempt produced. Quote the error
   message verbatim — paraphrasing loses the keyword that often is the
   root cause hint.

4. **Constraints (HARD).** Things the user has already rejected:
   - "Don't propose swapping the X model."
   - "Don't propose pay-per-token fallbacks."
   - "Don't propose 'wait and retry tomorrow' as the only answer."
   - "Don't propose trimming MVP enum / scope cuts."
   Codex defaults to scope-cut recommendations because that's the cheap
   answer for short-horizon problems. The user explicitly rejects this for
   long-horizon professional tools — encode the rejection in the prompt.

5. **Asks (numbered).** Specific questions, ordered. Each ask should
   produce a concrete artifact: a diff, a config, a citation, a
   confidence statement. Avoid open-ended "what do you think" asks.

6. **Output format.** "Korean explanation. Plain text, terminal-renderable.
   ≤500 words." Keep code in fenced blocks. Tail with one-line confidence
   statement. Without the explicit format directive Codex expands into
   long-form Markdown that bloats context.

## Common Codex behaviors to watch for

- **Scope-cut recommendations.** Codex will routinely suggest reducing
  enum size, deferring features to "post-MVP", merging stages. For Mythrill
  and similar long-horizon tools, the user has explicitly said
  "completeness > shortcut" and rejects these. Either pre-empt the cut in
  the prompt's HARD constraints, or surface the cut to the user verbatim
  and let them reject — never silently apply.

- **Sandbox file-write limits.** `codex exec` runs read-only by default.
  It can read files freely but cannot write. So the workflow is:
  Sub-Director writes the prompt → Codex extracts/decides → Sub-Director
  applies the change to disk. Don't ask Codex to write files; ask for the
  diff or the JSON.

- **AGENTS.md auto-injection.** Codex auto-injects ~10–30K tokens of
  AGENTS.md / SKILL.md content from `~/.codex/` and the working
  directory. This is fine for cost (it's subscription quota, not
  per-token), but it means Codex sees more context than you sent. If
  Codex makes a recommendation that contradicts what your prompt said,
  check whether AGENTS.md in scope had something that pulled it in the
  other direction.

- **Single-shot vs multi-turn.** `codex exec` is one-shot. For a
  multi-turn refinement (Codex proposes → user iterates), use the
  interactive `codex` REPL via tmux. The handoff prompt should be
  self-contained for one-shot use.

## Anti-patterns

- **Sending bare "what's wrong here" without state.** Codex will probe
  the filesystem, cost time and tokens, often miss the latest log because
  it doesn't know where logs land. Always include the captured log tail.

- **Re-rationalizing Codex output.** When Codex says "the deprecated SDK
  is the cause," do not present the user with "Codex thinks it might be
  the SDK but I'm not sure." Present Codex's conclusion verbatim and
  apply it. The user wants Director judgment, not Sub-Director re-filter.

- **Skipping the handoff because "I think I know the answer."** That's
  the trigger condition itself — Rule 14 says when you're cycling on
  external-cause guesses, you don't know. Hand it off.

## Provenance

Originating sessions:
- 2026-05-07: gemini-3.1-pro-preview thinking timeout. Opus cycled
  4 times on external-cause guesses (server load, transient capacity,
  retry-tomorrow). Codex single-shot identified the deprecated
  google.generativeai SDK as root cause; thinking_config unavailable
  in legacy SDK was the actual mechanism.
- 2026-05-07: LLM-2 second-spike plan review. Codex identified 4 gaps
  in the plan (eval criteria validity, sampling strategy, ground-truth
  source, constitutive-eq scope), exactly the gaps a separate Sub-Director
  review would have produced — but in 1 codex invocation instead of a
  multi-turn debate.
- 2026-05-07: Gemini 503 retry harness. Codex produced a complete
  exponential-backoff patch with citations to AI Studio docs in the
  same response.

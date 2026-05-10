---
title: Validators — On-demand validation pattern
created: 2026-05-04
updated: 2026-05-06
type: architecture
tags: [multi-agent, validation, qa, automation]
sources:
  - "[[roles]]"
  - "Alex AI Multi LLM Agent video (nJfqO5edMFk) — Validator pattern derivation"
confidence: medium
---

# Validators

Not a separate role slot — a pattern where, whenever validation is needed, an available LLM generates and runs a validation script on the spot.

## Triggers

Invoke a Validator when any of the following occurs:

- Engine Programmer produces code, before merge
- Tech Artist produces a natural-language → parameter conversion artifact
- Just before R&D Engineer consensus claims are written to wiki — format/link check
- Check C-Chasm IP artifacts for [[c-chasm-five-laws]] violations
- Mythrill regression tests (e.g., 30-run 100% pass)

## Operation

1. Caller passes the validation target (file path or result) and the validation criteria
2. Validator LLM (a) converts criteria into explicit propositions (b) writes a Python/shell validation script (c) executes (d) reports results
3. Scripts saved at `~/.hermes/wiki/architecture/validators/scripts/` (reusable)
4. Result returned to caller; only proceed to next step on pass

## LLM Tier Matching

| Validation type | Recommended Tier ([[cost-tiers]]) |
|---|---|
| File existence · format · numeric threshold | Tier 3 (local) or Tier 4 (script) |
| Quantitative regression (numeric compare) | Tier 4 (pytest) |
| Semantic validation (IP rule violation, conventions) | Tier 1 or Tier 2 |
| Security · vulnerability scan | Tier 4 (dedicated tools) + Tier 2 (interpretation) |

## Script Accumulation

- Location: `~/.hermes/wiki/architecture/validators/scripts/`
- Naming: `validate_<target>_<criterion>.py`
- Reuse: when the same criterion recurs, call the existing script instead of generating a new one

## Filling the Unassigned Slot

In [[roles]], Validator is marked "not an LLM slot." It's a pattern, not a rank.
However, semantic validation may be temporarily performed by whichever Frontier/Strong model is available at call time.

## Related Docs

- [[roles]] · [[cost-tiers]] · [[model-prompting-conventions]]

# Gemini "*-preview" thinking model availability is volatile

## TL;DR

`gemini-3.1-pro-preview` and other `*-pro-preview` thinking-class Gemini
models can pass 50/50 tests one week and time out 0/5 the next, even on
identical short inputs and identical SDK call patterns. The non-thinking
sister model `gemini-3-flash-preview` keeps responding in ~2 s under the
same key. This is a Google-side capacity / preview-instability signal,
not a key, SDK, prompt, or quota fault.

When this happens, do NOT silently swap models or remove Gemini from the
matrix. Diagnose first, then bring the user the choice.

## Symptoms (observed 2026-05-07, Mythrill MVP demo run)

Same Python script, same `~/mythrill-pipeline/.env`, same prompt
template, same 5 short inputs:

| Date          | Model                       | Result            |
|---------------|-----------------------------|-------------------|
| 2026-05-02    | `gemini-3.1-pro-preview`    | 50/50 schema_ok    |
| 2026-05-07    | `gemini-3.1-pro-preview`    | 0/5 — 4× HTTP 504 "Deadline expired", 1× HTTP 503 "currently experiencing high demand" |
| 2026-05-07    | `gemini-3-flash-preview`    | OK in 1.9 s on a 13-byte ping prompt |

The thinking model never returned, even on a "Say only: PING" 13-byte
input, with the SDK's default 600 s timeout.

Key rotation (new GCP project, fresh API key) did NOT change the
outcome — confirms the bottleneck is the model endpoint, not the
project quota or the auth chain.

## Diagnostic recipe (run this before deciding anything)

This is the minimal probe to separate "key/SDK/quota broken" from
"this specific preview endpoint is unhealthy":

```bash
cd ~/mythrill-pipeline && source venv/bin/activate
python - <<'PY'
import os, time
from dotenv import load_dotenv
load_dotenv('.env')
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

for mn in ['gemini-3-flash-preview', 'gemini-3-pro-preview', 'gemini-3.1-pro-preview']:
    t0 = time.time()
    try:
        r = genai.GenerativeModel(mn).generate_content('Say only: PING')
        print(f'OK  {mn} {time.time()-t0:5.1f}s -> {r.text[:60]!r}')
    except Exception as e:
        print(f'FAIL {mn} {time.time()-t0:5.1f}s {type(e).__name__}: {str(e)[:100]}')
PY
```

Decision tree based on the result row for `gemini-3.1-pro-preview`:

- `OK ... < 30 s` → endpoint healthy now, original failure was transient,
  re-run the real workload.
- `OK ... > 60 s` → thinking model is alive but slow; the original
  pipeline's per-call SDK timeout (600 s default) is enough but the
  user's wall-clock cost is real. Surface this to the user before
  fanning out 30+ inputs.
- `FAIL ... 504 / 503 / DEADLINE_EXCEEDED` on the pro-preview AND `OK`
  on `gemini-3-flash-preview` → endpoint is unhealthy on Google's side.
  Stop. Bring options to the user (see below).
- `FAIL` on every model → check key, SDK, network, quota; do NOT
  conclude "Gemini broken" yet.

## Forbidden self-corrections

The following are explicit anti-patterns when this happens (recorded
because they cost a real session 30+ minutes on 2026-05-07):

1. Adding `request_options={"timeout": 120}` or
   `max_output_tokens=2048` "to fix the hang." The SDK default is
   already 600 s. Tightening the timeout makes the failure look like
   *your* timeout, not the endpoint's. The original 50/50 v3 baseline
   was achieved with NO timeout override — match that to make
   regressions diagnosable.

2. Killing a long-running call after N minutes because "it must be
   stuck." A thinking model on a multi-stage Korean prompt can legitimately
   take 5+ minutes per call. Don't kill it unless the user agreed
   beforehand on a hard wall-clock budget.

3. Silently removing Gemini from the matrix and continuing with
   Claude+DeepSeek "to make progress." The user's published validation
   matrix and submission form may have specifically named the three
   models; dropping one without explicit consent invalidates the
   experiment AND the submission. Bring the option, do not take it.

4. Swapping `gemini-3.1-pro-preview` → `gemini-3-pro-preview` or
   `gemini-2.5-pro` "as a near-equivalent." These are different model
   tiers with different reasoning behavior. Substitution requires the
   user to update their writeup, not for the agent to decide.

## Options to surface when the pro-preview is down

Phrase them as a numbered choice, do not pick one:

1. **Retry later (same model)** — preview endpoints often recover on
   their own. Cheap, slow.
2. **Switch SDK** — the deprecated `google.generativeai` package
   prints a `FutureWarning` recommending `google.genai`. The new SDK
   exposes streaming options that might side-step the 504 path. Code
   change required.
3. **Drop Gemini for this run, mark the result row as "endpoint
   unavailable on YYYY-MM-DD"** — preserves the experiment by being
   explicit about the gap, instead of producing a silent 0/N row that
   looks like a model failure.
4. **Substitute with a sibling model** (e.g. `gemini-3-pro-preview`
   if 3.1 specifically is dead) — only if the user's writeup permits
   it. Note in the result CSV which sibling was substituted.

## Reference: model identifier hygiene

Check valid identifiers before assuming a typo:

```python
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
```

The 2026-05-07 environment listed:

- `models/gemini-3-pro-preview`
- `models/gemini-3-flash-preview`
- `models/gemini-3.1-pro-preview`
- `models/gemini-3.1-pro-preview-customtools`
- `models/gemini-3.1-flash-lite-preview`
- `models/gemini-3-pro-image-preview`
- `models/gemini-3.1-flash-image-preview`
- `models/gemini-3.1-flash-tts-preview`

`gemini-3.1-pro-preview` and `gemini-3.1-pro-preview-customtools` are
NOT the same endpoint — the latter is tools-tuned and behaves
differently on free-text prompts. If diagnosing a "wrong model"
hypothesis, probe both.

## SDK migration note

`google.generativeai` is deprecated in favor of `google.genai`. The
`FutureWarning` is loud but does not change call behavior yet. When
fixing this code path, check whether the new SDK lets you set a
`thinking_config={"thinking_budget": 0}` or stream tokens — both can
sidestep the 504-class failures by either disabling the thinking step
or starting to receive partial output before the deadline.

Migration is a separate task, not a "fix the timeout" patch.

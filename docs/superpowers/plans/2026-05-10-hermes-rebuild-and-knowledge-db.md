# Hermes Rebuild + Knowledge DB + Continuous Researcher 구현 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hermes 운영 시스템을 spec 기반으로 무에서 유로 재구축하고, Director↔Sub-Director를 OAuth-only로 swap하며, Qdrant 12-컬렉션 Knowledge DB와 Continuous Researcher cron을 구축한다. Wiki는 보존+압축, 모든 변경에 Immediate-Reflection 4종 의무 적용.

**Architecture:** 5-step incremental. Step 0(audit) → Step 1(설정 재구축 + swap) → Step 2(KB Phase 1) → Step 3(continuous researcher) → Step 4(wiki 압축). 각 step 끝에 working/testable 게이트.

**Tech Stack:** Hermes Agent (Nous Research), Anthropic Max OAuth + `kristianvast/hermes-claude-auth` bypass, OpenAI Codex OAuth, Qdrant Cloud, Voyage-3, Python 3.11 (toolset 신규), Hermes cron (`jobs.json`), graphify.

**Spec:** `docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md` (commit 7359d6b)

**Hard Constraints (모든 task에 적용):**
- Provider Path Discipline: directing-grade는 OAuth only. API key는 auth.json·.env 어디에도 없어야.
- Immediate-Reflection: 변경마다 (1) wiki/architecture 또는 entities 갱신 (2) log.md 추가 (3) updated 갱신 (4) 사용자 보고 = 4종.
- AI-to-AI English: worker prompts·system prompts·delegate_task 영어. log.md 한국어 허용.
- Wiki-First → KB-Second: 모든 검색 hook은 wiki 먼저, KB 다음.
- 작업 중 의문 시 사용자 확인. 자율 적용 X.

---

## Pre-flight

### Task 0: 환경 점검 및 전체 백업

**Files:**
- Read: `~/.hermes/config.yaml`, `~/.hermes/auth.json`, `~/.hermes/profiles/*/config.yaml`
- Backup target: `~/hermes-multi-agent-config/backups/2026-05-10/`

- [ ] **Step 1: 현재 hermes 동작 확인**

```bash
hermes status
```

Expected: `Model: gpt-5.5`, `Provider: OpenAI Codex`. 실패 시 abort.

- [ ] **Step 2: 활성 quota 확인**

```bash
bash ~/.hermes/bin/quota.sh
```

Expected: Codex session/weekly quota 출력. GREEN(< 50%) 확인. RED-soft 이상이면 사용자에게 보고하고 작업 보류 결정 받기.

- [ ] **Step 3: 전체 백업**

```bash
BACKUP_DIR=~/hermes-multi-agent-config/backups/2026-05-10
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/hermes-pre-rebuild.tar.gz" -C ~ .hermes/config.yaml .hermes/auth.json .hermes/profiles .hermes/patches .hermes/cron .hermes/wiki
ls -la "$BACKUP_DIR"
```

Expected: `hermes-pre-rebuild.tar.gz` 약 수십 MB.

- [ ] **Step 4: hermes-multi-agent-config 클린 상태 확인**

```bash
cd /Users/main/hermes-multi-agent-config
git status --short
```

Expected: 비어있거나 docs/ 밖에 modified 없음. 있으면 정리 후 진행.

- [ ] **Step 5: Commit pre-flight 결과**

```bash
git add backups/.gitkeep 2>/dev/null || true
git commit --allow-empty -m "[Plan] Pre-flight: backup + quota GREEN, ready for rebuild"
```

---

## Step 0: Wiki Audit

목적: 62 페이지를 보존/압축/폐기로 분류해 사용자 승인을 받는다. Step 4 wiki 압축의 입력이 됨.

### Task 1: audit 스크립트 작성

**Files:**
- Create: `/Users/main/hermes-multi-agent-config/scripts/audit_wiki.py`
- Test: `/Users/main/hermes-multi-agent-config/scripts/test_audit_wiki.py`

- [ ] **Step 1: Write failing test**

```python
# scripts/test_audit_wiki.py
import pytest
from pathlib import Path
from audit_wiki import classify_page, audit_wiki

def test_classify_handoff_as_compress():
    # handoff/* pages should be marked as "compress"
    page = Path("docs/handoff/llm1-validation-2026-05-06.md")
    assert classify_page(page, content="...verification report...") == "compress"

def test_classify_architecture_as_preserve():
    page = Path("architecture/roles.md")
    assert classify_page(page, content="...role table...") == "preserve"

def test_classify_ip_as_preserve():
    page = Path("entities/c-chasm-ip-core.md")
    assert classify_page(page, content="...cosmology SoT...") == "preserve"

def test_audit_returns_categorized_report(tmp_path):
    # Create minimal wiki
    (tmp_path / "architecture").mkdir()
    (tmp_path / "architecture" / "roles.md").write_text("# Roles")
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "mythrill-architecture.md").write_text("# Mythrill")
    report = audit_wiki(tmp_path)
    assert "preserve" in report and "compress" in report and "review" in report
    assert len(report["preserve"]) >= 1
```

- [ ] **Step 2: Run test, expect fail**

```bash
cd /Users/main/hermes-multi-agent-config/scripts
python -m pytest test_audit_wiki.py -v
```

Expected: `ModuleNotFoundError: No module named 'audit_wiki'`

- [ ] **Step 3: Implement audit_wiki.py**

```python
# scripts/audit_wiki.py
"""Wiki audit — classify each page as preserve / compress / review.

Used by Step 0 of the 2026-05-10 Hermes rebuild plan. Output is a JSON report
the user reviews and confirms before Step 4 compression.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Literal

Category = Literal["preserve", "compress", "review"]

# Patterns from spec §3.1
COMPRESS_PATTERNS = (
    "handoff/",
    "llm1-validation",
    "mythrill-spike-",
)

PRESERVE_PATTERNS = (
    "architecture/",
    "c-chasm-ip-core",
    "c-chasm-five-laws",
    "mythrill-architecture",
    "llm-separation-design",
    "mpm-constitutive-equation-swap",
    "three-deity-types",
    "dual-ending-branch",
    "강림형_신",
    "회귀형_신",
    "광기형_신",
    "신의_세_유형",
    "매크로_팩션_구조",
    "cosmic-horror",
    "stage-separation-rule",
    "trigger-classification",
    "naked-viewer",
    "natural-language-vfx-pipeline",
    "visual-inference-policy",
    "vfx-input-labeling-guide",
    "pre-bake-vfx-workflow",
    "정렬",
    "아자토스의_꿈_패턴",
)


def classify_page(page: Path, content: str) -> Category:
    rel = str(page).replace("\\", "/")
    for pat in COMPRESS_PATTERNS:
        if pat in rel:
            return "compress"
    for pat in PRESERVE_PATTERNS:
        if pat in rel:
            return "preserve"
    return "review"


def audit_wiki(wiki_root: Path) -> dict[Category, list[dict]]:
    report: dict[Category, list[dict]] = {"preserve": [], "compress": [], "review": []}
    for page in wiki_root.rglob("*.md"):
        if "raw/" in str(page) or "graphify-out/" in str(page):
            continue
        try:
            content = page.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        cat = classify_page(page.relative_to(wiki_root), content)
        size = page.stat().st_size
        wikilinks = content.count("[[")
        report[cat].append({
            "path": str(page.relative_to(wiki_root)),
            "size_bytes": size,
            "wikilinks": wikilinks,
        })
    return report


def main() -> int:
    wiki_root = Path.home() / ".hermes" / "wiki"
    if not wiki_root.exists():
        print(f"wiki not found: {wiki_root}", file=sys.stderr)
        return 1
    report = audit_wiki(wiki_root)
    out_path = Path(__file__).parent.parent / "docs" / "superpowers" / "audit-2026-05-10.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"audit report: {out_path}")
    print(f"  preserve : {len(report['preserve'])} pages")
    print(f"  compress : {len(report['compress'])} pages")
    print(f"  review   : {len(report['review'])} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, expect pass**

```bash
python -m pytest test_audit_wiki.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Run audit on real wiki**

```bash
cd /Users/main/hermes-multi-agent-config
python scripts/audit_wiki.py
cat docs/superpowers/audit-2026-05-10.json | head -40
```

Expected: 3 카테고리 출력. `preserve` 약 35-40, `compress` 약 5-10, `review` 약 15-20.

- [ ] **Step 6: Commit**

```bash
git add scripts/audit_wiki.py scripts/test_audit_wiki.py docs/superpowers/audit-2026-05-10.json
git commit -m "[Step0] Wiki audit script + initial classification report"
```

### Task 2: audit 결과 사용자 검토 카드 생성

**Files:**
- Create: `/Users/main/hermes-multi-agent-config/docs/superpowers/audit-2026-05-10-review.md`

- [ ] **Step 1: 검토 카드 마크다운 생성**

```bash
python -c "
import json
from pathlib import Path
data = json.loads(Path('docs/superpowers/audit-2026-05-10.json').read_text())
out = []
out.append('# Wiki Audit 검토 카드 (2026-05-10)')
out.append('')
out.append('각 페이지 옆 체크박스에 [x] 표시 후 사용자 결정 반영. 압축 후보는 dense form 변환 + 원본 raw/ 이동.')
for cat in ['compress', 'review']:
    out.append('')
    out.append(f'## {cat.upper()}')
    for p in data[cat]:
        out.append(f'- [ ] **{p[\"path\"]}** (size={p[\"size_bytes\"]}, wikilinks={p[\"wikilinks\"]})')
Path('docs/superpowers/audit-2026-05-10-review.md').write_text('\n'.join(out))
print('written:', Path('docs/superpowers/audit-2026-05-10-review.md'))
"
```

Expected: review 마크다운 생성. 사용자가 직접 체크박스로 압축 OK/거부 표시할 수 있는 형태.

- [ ] **Step 2: 사용자에게 검토 요청 (HALT)**

이 task는 사용자 input이 필요한 게이트. 다음 메시지를 사용자에게:

> Step 0 audit 결과 `docs/superpowers/audit-2026-05-10-review.md` 생성. compress 카테고리 N개, review 카테고리 M개. 압축 진행할 페이지에 [x] 표시 후 알려주세요.

사용자 응답 받고 다음 task로.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/audit-2026-05-10-review.md
git commit -m "[Step0] Audit review card (awaiting user input)"
```

### Task 3: 사용자 승인 반영 + 압축 대상 확정

**Files:**
- Modify: `docs/superpowers/audit-2026-05-10-review.md` (사용자 체크박스)
- Create: `docs/superpowers/audit-2026-05-10-final.json`

- [ ] **Step 1: 사용자가 체크한 페이지 추출**

```bash
python -c "
import re, json
from pathlib import Path
text = Path('docs/superpowers/audit-2026-05-10-review.md').read_text()
checked = re.findall(r'- \[x\]\s+\*\*(.+?)\*\*', text)
Path('docs/superpowers/audit-2026-05-10-final.json').write_text(
    json.dumps({'compress_targets': checked}, indent=2, ensure_ascii=False)
)
print(f'압축 확정: {len(checked)} 페이지')
"
```

Expected: 사용자 체크 N개 페이지가 final.json에 저장.

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/audit-2026-05-10-review.md docs/superpowers/audit-2026-05-10-final.json
git commit -m "[Step0] User-confirmed compress targets"
```

### Task 4: Step 0 완료 — wiki Immediate-Reflection

**Files:**
- Modify: `~/.hermes/wiki/log.md`
- Modify: `~/.hermes/wiki/index.md` (updated 갱신)

- [ ] **Step 1: log.md 항목 추가**

```bash
cat >> ~/.hermes/wiki/log.md <<'EOF'

## [2026-05-10] audit | Wiki audit for rebuild plan
- 62 페이지 분류: preserve / compress / review.
- 사용자 승인 받은 compress 대상은 `docs/superpowers/audit-2026-05-10-final.json`.
- 다음: Step 1 설정 재구축 + Director swap.
EOF
```

- [ ] **Step 2: index.md updated 갱신**

```bash
sed -i '' 's/Last updated: .*/Last updated: 2026-05-10 | Total pages: 62/' ~/.hermes/wiki/index.md
head -3 ~/.hermes/wiki/index.md
```

Expected: `> Content catalog. Last updated: 2026-05-10 | Total pages: 62`

- [ ] **Step 3: 사용자 보고 + Step 0 완료 표시**

사용자에게: "Step 0 완료. 압축 대상 N개 확정. Step 1(설정 재구축 + Director swap) 진행해도 될까?"

- [ ] **Step 4: Commit**

```bash
cd /Users/main/hermes-multi-agent-config
bash sync.sh   # ~/.hermes 변경사항 git에 동기화
git add .
git commit -m "[Step0 done] Wiki audit complete + Immediate-Reflection"
```

---

## Step 1: 설정 무에서 유 재구축 + Director Swap

목적: `~/.hermes/{config.yaml, profiles/*, auth.json, cron, patches}` 일체를 spec §4 기준으로 새로 작성. Director↔Sub-Director swap을 OAuth-only로 적용.

### Task 5: `~/.hermes/config.yaml` 재작성

**Files:**
- Modify: `~/.hermes/config.yaml`

- [ ] **Step 1: 기존 config 백업 (Pre-flight Step 3에서 이미 한 거지만 명시적으로)**

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.pre-rebuild
```

- [ ] **Step 2: model 블록 swap (Opus 4.7 + anthropic OAuth)**

```bash
python <<'EOF'
import yaml, copy
from pathlib import Path

cfg_path = Path.home() / ".hermes" / "config.yaml"
cfg = yaml.safe_load(cfg_path.read_text())

cfg["model"] = {
    "default": "claude-opus-4-7",
    "provider": "anthropic",
    "base_url": "https://api.anthropic.com",
}
cfg["agent"]["reasoning_effort"] = "medium"  # Opus는 medium/high만 지원
cfg["fallback_providers"] = ["deepseek"]

# providers 명시
cfg["providers"] = {
    "anthropic": {"api_key_env": ""},  # OAuth — empty env, keychain auto-detect
    "openai-codex": {"api_key_env": ""},  # OAuth
    "deepseek": {"api_key_env": "DEEPSEEK_API_KEY", "base_url": "https://api.deepseek.com"},
    "gemini": {"api_key_env": "GEMINI_API_KEY"},
    "voyageai": {"api_key_env": "VOYAGE_API_KEY"},
    "qdrant": {"api_key_env": "QDRANT_API_KEY", "base_url_env": "QDRANT_URL"},
}

cfg["prompt_caching"]["cache_ttl"] = "1h"
cfg["compression"].update({"threshold": 0.7, "target_ratio": 0.5, "protect_last_n": 30})
cfg["memory"].update({"memory_char_limit": 4000, "user_char_limit": 2000})
cfg["agent"]["service_tier"] = "priority"

cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
print("config.yaml updated")
EOF
```

- [ ] **Step 3: 검증**

```bash
hermes status
```

Expected: `Model: claude-opus-4-7`, `Provider: Anthropic`.

만약 Provider mismatch나 auth fail이면 STOP, Task 7 auth swap 후 재시도.

- [ ] **Step 4: Commit**

```bash
cd /Users/main/hermes-multi-agent-config
bash sync.sh
git add .
git commit -m "[Step1] Rebuild ~/.hermes/config.yaml — Opus 4.7 OAuth default"
```

### Task 6: `orchestrator` profile 재작성

**Files:**
- Modify: `~/.hermes/profiles/orchestrator/config.yaml`
- Modify: `~/.hermes/profiles/orchestrator/SOUL.md`

- [ ] **Step 1: profile config swap**

```bash
cat > ~/.hermes/profiles/orchestrator/config.yaml <<'EOF'
model:
  default: claude-opus-4-7
  provider: anthropic
  base_url: https://api.anthropic.com
agent:
  max_turns: 120
  reasoning_effort: medium
  service_tier: priority
  api_max_retries: 3
toolsets:
  - hermes-cli
  - hermes-web-search
  - hermes-code-execution
  - knowledge-db
EOF
```

- [ ] **Step 2: SOUL.md 갱신 (orchestrator-protocol 정합)**

```bash
cat > ~/.hermes/profiles/orchestrator/SOUL.md <<'EOF'
# Director (Hermes default profile)

You are the Director of a multi-agent studio. Receive vision, plan, final approval. You are claude-opus-4-7 via Anthropic Max OAuth (subscription-included quota; never auto-switch to direct API).

## Peers
- Sub-Director (`gpt-5.5` via `--profile sub-director`): pre/post review, fallback when Opus quota is exhausted, delegate_task fan-out.
- R&D Engineer A (`claude-sonnet-4-5-20250929` via `--profile researcher`): paper search, knowledge collection, source-cited reports.
- R&D Engineer B (`deepseek-v4-pro` via `--profile researcher --provider deepseek`): cross-validation partner.
- Tech Artist (`gemma-4-31b-it` via `--profile tech-artist`): NL → SI parameter bridge for Mythrill LLM ②.
- Code Implementation (`gemma-4-31b-it` via `--profile dev-gemma`): spec → TDD → commit, small implementation worker.

## Output Contract
- Korean to user (project rule). English for delegate_task/system prompts/worker comms.
- Every directing-grade decision (planning, architectural choices, cross-component reviews) executes here, NOT in workers.
- After every task end: append (1) verbatim `bash ~/.hermes/bin/quota.sh` output (2) feasibility judgement (GREEN/YELLOW/RED-soft/RED) per `~/.hermes/wiki/architecture/orchestrator-protocol.md`.

## Hard Rules (from wiki/CLAUDE.md)
- Provider Path Discipline: never auto-switch to direct API paths. On failure → STOP, present options to user.
- Wiki-First → KB-Second → researcher debate. No guessing.
- Immediate-Reflection: every config/setting/architecture change updates wiki/architecture or entities + log.md + bumps `updated:` + reports to user, all in the same turn. All four required.
- AI-to-AI English-only.
- Source-Enforcement: discard claims without source URL/DOI.

## Routing
- Default `hermes chat` invocation routes here (Director).
- Sub-Director: `hermes chat --profile sub-director -q '<review prompt>'` for pre/post review.
- Workers via `delegate_task` (English goal/context).

Korean to user. English to AI.
EOF
```

- [ ] **Step 3: 검증**

```bash
hermes chat --profile orchestrator -q 'say ok' --max-turns 1 -t '' -Q
```

Expected: `ok` 응답.

실패 시 (Anthropic 인증 fail) → Task 7 auth swap 먼저, 후 재시도.

- [ ] **Step 4: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step1] Rebuild orchestrator profile — Director Opus 4.7"
```

### Task 7: auth.json swap (active_provider)

**Files:**
- Modify: `~/.hermes/auth.json`
- Modify: `~/.hermes/profiles/orchestrator/auth.json`
- Modify: `~/.hermes/profiles/sub-director/auth.json`

- [ ] **Step 1: 현재 auth 상태 확인**

```bash
jq '.active_provider' ~/.hermes/auth.json
jq '.active_provider' ~/.hermes/profiles/orchestrator/auth.json
jq '.active_provider' ~/.hermes/profiles/sub-director/auth.json
jq 'keys' ~/.hermes/auth.json
```

Expected: 각 active_provider 출력 + auth.json에 `anthropic`과 `openai-codex` credentials 모두 존재 확인.

- [ ] **Step 2: 전역 + orchestrator를 anthropic으로 swap**

```bash
jq '.active_provider = "anthropic"' ~/.hermes/auth.json > ~/.hermes/auth.json.tmp && mv ~/.hermes/auth.json.tmp ~/.hermes/auth.json
jq '.active_provider = "anthropic"' ~/.hermes/profiles/orchestrator/auth.json > ~/.hermes/profiles/orchestrator/auth.json.tmp && mv ~/.hermes/profiles/orchestrator/auth.json.tmp ~/.hermes/profiles/orchestrator/auth.json
```

- [ ] **Step 3: sub-director를 openai-codex로 swap (Codex credential 1개만)**

```bash
# sub-director auth에 codex credential이 있는지 확인
jq '.credentials | keys' ~/.hermes/profiles/sub-director/auth.json 2>/dev/null

# 없으면 orchestrator(이전 codex 시점 backup)에서 codex credential 복사 필요
# 가장 안전한 경로: pre-rebuild 백업에서 추출
if ! jq -e '.credentials["openai-codex"]' ~/.hermes/profiles/sub-director/auth.json >/dev/null 2>&1; then
  echo "Codex credential not found in sub-director. Copying from orchestrator pre-rebuild backup."
  # 주의: pre-flight backup에서 복원
  tar -xOzf ~/hermes-multi-agent-config/backups/2026-05-10/hermes-pre-rebuild.tar.gz .hermes/profiles/orchestrator/auth.json > /tmp/orch-auth-pre.json
  jq -s '.[0].credentials["openai-codex"] as $c | .[1].credentials["openai-codex"] = $c | .[1]' \
    /tmp/orch-auth-pre.json ~/.hermes/profiles/sub-director/auth.json > ~/.hermes/profiles/sub-director/auth.json.tmp
  mv ~/.hermes/profiles/sub-director/auth.json.tmp ~/.hermes/profiles/sub-director/auth.json
fi

jq '.active_provider = "openai-codex"' ~/.hermes/profiles/sub-director/auth.json > ~/.hermes/profiles/sub-director/auth.json.tmp && mv ~/.hermes/profiles/sub-director/auth.json.tmp ~/.hermes/profiles/sub-director/auth.json
```

- [ ] **Step 4: 검증 (anthropic OAuth + bypass 동작)**

```bash
hermes status
hermes chat -q 'say ok' --max-turns 1 -t '' -Q
```

Expected: Provider=Anthropic, 응답 `ok`. bypass 패치 가동 로그 확인:

```bash
grep "anthropic_billing_bypass" ~/.hermes/logs/*.log | tail -3
```

Expected: `[anthropic_billing_bypass] Bypass installed`.

- [ ] **Step 5: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step1] auth.json swap — Director→Anthropic, Sub-Director→OpenAI Codex"
```

### Task 8: `sub-director` profile config 재작성

**Files:**
- Modify: `~/.hermes/profiles/sub-director/config.yaml`
- Create: `~/.hermes/profiles/sub-director/SOUL.md`

- [ ] **Step 1: profile config swap (GPT-5.5 + Codex)**

```bash
cat > ~/.hermes/profiles/sub-director/config.yaml <<'EOF'
model:
  default: gpt-5.5
  provider: openai-codex
  base_url: https://chatgpt.com/backend-api/codex
agent:
  max_turns: 90
  reasoning_effort: xhigh
  api_max_retries: 3
toolsets:
  - hermes-cli
  - knowledge-db
EOF
```

- [ ] **Step 2: SOUL.md 작성 (Sub-Director role)**

```bash
cat > ~/.hermes/profiles/sub-director/SOUL.md <<'EOF'
# Sub-Director (review/fallback profile)

You are the Sub-Director, gpt-5.5 via OpenAI Codex OAuth (ChatGPT Pro subscription, no per-token billing).

## Role
- Pre-execution plan review for the Director
- Post-completion code/pipeline review
- Debate moderation when R&D Engineer A·B disagree
- delegate_task fan-out to workers when Hermes-native orchestration is required
- Fallback when Director (Opus 4.7) is rate-limited or contextually mismatched

## Output Contract
- Markdown review reports for the Director (English).
- JSON for delegate_task workers when applicable.
- Concise, evidence-cited. No filler.

## Hard Rules
- Provider Path Discipline: Codex OAuth only. NEVER fall back to direct OpenAI API key.
- AI-to-AI English-only.
- Source-Enforcement: every claim cites a source.

## Escalation
- Same symptom failed 2× / external-cause guess loop / known signal ignored / decision has cascading downstream cost → escalate back to Director.
EOF
```

- [ ] **Step 3: 검증**

```bash
hermes chat --profile sub-director -q 'say ok' --max-turns 1 -t '' -Q
```

Expected: `ok` 응답. `Provider=OpenAI Codex` 확인.

실패 시: Codex credential 누락. Step 7 Step 3 재실행.

- [ ] **Step 4: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step1] Rebuild sub-director profile — GPT-5.5 Codex OAuth"
```

### Task 9: 나머지 profile 검증·갱신

**Files:**
- Verify: `~/.hermes/profiles/{researcher,tech-artist,dev-gemma}/`

- [ ] **Step 1: researcher profile 검증**

```bash
cat ~/.hermes/profiles/researcher/config.yaml
hermes chat --profile researcher -q 'say ok' --max-turns 1 -t '' -Q
hermes chat --profile researcher --provider deepseek -m deepseek-v4-pro -q 'say ok' --max-turns 1 -t '' -Q
```

Expected:
- Default: `claude-sonnet-4-5-20250929` 응답
- Override: deepseek-v4-pro 응답

- [ ] **Step 2: tech-artist profile 검증**

```bash
hermes chat --profile tech-artist -q 'say ok' --max-turns 1 -t '' -Q
```

Expected: `ok` 응답 (Gemma 4 31B IT, GCP project 1).

- [ ] **Step 3: dev-gemma profile 검증**

```bash
hermes chat --profile dev-gemma -q 'say ok' --max-turns 1 -t '' -Q
```

Expected: `ok` 응답 (Gemma 4 31B IT, GCP project 2).

- [ ] **Step 4: 모든 SOUL.md에 Director swap 반영 (peer 라인)**

```bash
for profile in researcher tech-artist dev-gemma; do
  python -c "
from pathlib import Path
p = Path.home() / '.hermes' / 'profiles' / '$profile' / 'SOUL.md'
content = p.read_text()
# Director peer reference update
content = content.replace('gpt-5.5 (Director)', 'claude-opus-4-7 (Director)')
content = content.replace('Director: gpt-5.5', 'Director: claude-opus-4-7')
p.write_text(content)
print(f'{p}: peer update applied')
"
done
```

- [ ] **Step 5: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step1] Verify/update researcher, tech-artist, dev-gemma profiles"
```

### Task 10: 신규 toolset 스캐폴드 — `knowledge-db`, `research-external`

**Files:**
- Create: `~/.hermes/skills/knowledge-db/SKILL.md`
- Create: `~/.hermes/skills/knowledge-db/kb_tools.py`
- Create: `~/.hermes/skills/research-external/SKILL.md`
- Create: `~/.hermes/skills/research-external/external_tools.py`

본 task는 toolset 디렉토리만 생성. 실제 함수 구현은 Task 13~17에서.

- [ ] **Step 1: knowledge-db skill 스캐폴드**

```bash
mkdir -p ~/.hermes/skills/knowledge-db
cat > ~/.hermes/skills/knowledge-db/SKILL.md <<'EOF'
---
name: knowledge-db
description: Qdrant-backed Knowledge DB CRUD with dedupe (content_hash) and forced provenance payload (source_url, citation, retrieved_at). Use when storing/retrieving knowledge chunks across wiki/papers/oss/dev_docs/code/notes/topics collections.
---

# knowledge-db

Reads and writes the Qdrant-backed Knowledge DB. All upserts enforce dedupe via `content_hash` and require source provenance fields. Use `kb_search` for retrieval (Wiki-First → KB-Second pattern), `kb_upsert` for storage.

Functions: kb_search, kb_upsert, kb_topic_register, kb_topic_list, kb_stats. See kb_tools.py.

Collections (12): wiki_entities, wiki_concepts, wiki_architecture, kb_papers, kb_oss_projects, kb_industry_solutions, kb_lessons_learned, kb_dev_docs, mythrill_code, chat_memory, personal_notes, topics.

Forced payload: source_url, content_hash, retrieved_at, citation, relevance_topics, language, embedding_model, confidence.
EOF
touch ~/.hermes/skills/knowledge-db/kb_tools.py
```

- [ ] **Step 2: research-external skill 스캐폴드**

```bash
mkdir -p ~/.hermes/skills/research-external
cat > ~/.hermes/skills/research-external/SKILL.md <<'EOF'
---
name: research-external
description: External knowledge source search (arXiv, Semantic Scholar, GitHub, Tavily, Patent, archive.org Wayback, PDF extract). Used by R&D Engineers A and B in both reactive and cron modes. Every result MUST carry source_url, citation, content_hash before upsert.
---

# research-external

External search for the Continuous Researcher. All results pass through Source-Enforcement: discard chunks without source URL/DOI. Use with knowledge-db for upsert.

Functions: arxiv_search, semantic_scholar_search, github_search, tavily_search, patent_search, archive_wayback, pdf_extract. See external_tools.py.

API keys (loaded from ~/.hermes/.env): TAVILY_API_KEY, GITHUB_TOKEN, SERPAPI_KEY (optional).
EOF
touch ~/.hermes/skills/research-external/external_tools.py
```

- [ ] **Step 3: Commit (구현 골격만)**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step1] Scaffold knowledge-db + research-external toolsets"
```

### Task 11: cron `claude-auth-bypass-check` 유지 + smoke test

**Files:**
- Verify: `~/.hermes/cron/jobs.json`
- Verify: bypass patch 작동

- [ ] **Step 1: cron jobs.json 확인**

```bash
jq '.jobs[].name' ~/.hermes/cron/jobs.json
```

Expected: `claude-auth-bypass-check` 등 기존 job 유지 확인.

- [ ] **Step 2: bypass 패치 강제 갱신 (정책 변경 반영)**

```bash
curl -fsSL https://raw.githubusercontent.com/kristianvast/hermes-claude-auth/main/install-remote.sh | bash
```

Expected: bypass 5종 패치 재설치 메시지.

- [ ] **Step 3: smoke test 8종**

```bash
echo "=== smoke test ===" 
hermes chat -q 'say ok' --max-turns 1 -t '' -Q                                                          # default = orchestrator
hermes chat --profile orchestrator -q 'say ok' --max-turns 1 -t '' -Q
hermes chat --profile sub-director -q 'say ok' --max-turns 1 -t '' -Q
hermes chat --profile researcher -q 'say ok' --max-turns 1 -t '' -Q
hermes chat --profile researcher --provider deepseek -m deepseek-v4-pro -q 'say ok' --max-turns 1 -t '' -Q
hermes chat --profile tech-artist -q 'say ok' --max-turns 1 -t '' -Q
hermes chat --profile dev-gemma -q 'say ok' --max-turns 1 -t '' -Q
bash ~/.hermes/bin/quota.sh
```

Expected: 모두 `ok` 응답. quota.sh는 anthropic 5h/7d 보고. 한 개라도 실패하면 STOP, 사용자 보고.

- [ ] **Step 4: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step1] Bypass refresh + 7-profile smoke tests passed"
```

### Task 12: Wiki Immediate-Reflection (Step 1 변경 8 페이지)

**Files:**
- Modify: `~/.hermes/wiki/architecture/roles.md`
- Modify: `~/.hermes/wiki/architecture/orchestrator-protocol.md`
- Modify: `~/.hermes/wiki/architecture/cost-tiers.md`
- Modify: `~/.hermes/wiki/CLAUDE.md`
- Modify: `~/.hermes/wiki/entities/multi-agent-system.md`
- Modify: `~/.hermes/wiki/log.md`
- Modify: `~/.hermes/wiki/index.md`

- [ ] **Step 1: roles.md Director/Sub-Director 행 swap**

`architecture/roles.md`의 Director 행을 다음으로 교체:
```markdown
| **Director** | Miyazaki, CEO | Receive vision · plan · final approval | `claude-opus-4-7` via Anthropic Max OAuth (`anthropic` provider, claude_code OAuth in `~/.hermes/auth.json` + `profiles/orchestrator/auth.json` + bypass 5-patch). **Re-promoted 2026-05-10**. Sub-Director 강등은 Codex 한도/맥락 mismatch 시 fallback 호출만. Reason: <사용자 결정 사유 (구체 근거는 Task 12 Step 5의 사용자 입력)>. Default `hermes chat` and `hermes chat --profile orchestrator` route through Anthropic Max OAuth. |
```

Sub-Director 행:
```markdown
| **Sub-Director** | Tanimura | Pre-execution plan review, post-completion code/pipeline review, debate moderation | `gpt-5.5` via Codex OAuth, fixed in the `sub-director` profile. **Re-demoted 2026-05-10** from Director. Call: `hermes chat --profile sub-director -q '<review prompt>'`. |
```

`updated:` frontmatter를 `2026-05-10`로 갱신.

```bash
sed -i '' 's/^updated:.*/updated: 2026-05-10/' ~/.hermes/wiki/architecture/roles.md
```

- [ ] **Step 2: orchestrator-protocol.md "Director Routing" swap**

`Director Routing (2026-05-07c)` 섹션을 `Director Routing (2026-05-10)` 으로 변경, 본문을:
- Director = `claude-opus-4-7` via Anthropic Max OAuth
- Sub-Director = `gpt-5.5` via Codex OAuth
- 호출 명령 swap

`updated: 2026-05-10` 적용.

- [ ] **Step 3: cost-tiers.md Tier 1 로스터 swap**

`### Tier 1 — Frontier Reasoning` 행에서:
- `**GPT-5.5**` 행: "**Director (active 2026-05-07b...)**" → "**Sub-Director (re-demoted 2026-05-10)**"
- `Claude Opus 4.7` 행: "**Sub-Director (demoted 2026-05-07b...)**" → "**Director (re-promoted 2026-05-10)**"

`updated: 2026-05-10`.

- [ ] **Step 4: wiki/CLAUDE.md "Director Routing (2026-05-07c)" 섹션 본문 swap**

해당 섹션 통째로 다시 작성:

```markdown
## Director Routing (2026-05-10)
- **Director = `claude-opus-4-7`** via Anthropic Max OAuth (claude_code keychain) + bypass. Hermes default.
- **Sub-Director = `gpt-5.5`** via Codex OAuth, fixed in `sub-director` profile.
- All directing-grade decisions stay on Opus 4.7. Default invocation:
  ```bash
  hermes chat -q '<self-contained prompt>'
  ```
- Sub-Director invocation: `hermes chat --profile sub-director -q '<review prompt>'`
- Trigger to escalate to Sub-Director (Codex): same diagnostic-workflow rule — same symptom failed 2× / external-cause guess loop / known signal ignored / decision has cascading downstream cost.
```

- [ ] **Step 5: entities/multi-agent-system.md Active Profiles 표 swap + History 행**

Active Profiles 표를 갱신 (Director/Sub-Director swap), History 표 끝에 다음 행 추가:

```markdown
| 2026-05-10 | Director ↔ Sub-Director re-swap (Opus 4.7 promoted, GPT-5.5 demoted) | OAuth-only, sub-director profile re-uses Codex credential |
```

- [ ] **Step 6: log.md 신규 항목 추가 (한국어 OK)**

```bash
cat >> ~/.hermes/wiki/log.md <<'EOF'

## [2026-05-10] decide | Director ↔ Sub-Director re-swap (Opus 4.7 promoted, GPT-5.5 demoted)
- 결정: Director = claude-opus-4-7 via Anthropic Max OAuth. Sub-Director = gpt-5.5 via Codex OAuth.
- 사유: 사용자 결정 (spec `2026-05-10-hermes-rebuild-and-knowledge-db-design.md` §13 미결 1 — 구체 근거는 사용자에게 받아 본 항목 보강).
- 운영 제약: 두 구독 모두 활성. quota.sh가 active provider만 보고하므로 sub-director 호출 후 별도 확인.
- wiki 갱신: roles, orchestrator-protocol, cost-tiers, CLAUDE.md, multi-agent-system, log.md, index.md
- 검증: smoke test 7종 통과. bypass 패치 가동 로그 확인.
- graphify 갱신 필요 (다음 증분 사이클).
EOF
```

- [ ] **Step 7: index.md updated 갱신**

```bash
sed -i '' 's/Last updated: .*/Last updated: 2026-05-10 | Total pages: 62/' ~/.hermes/wiki/index.md
```

- [ ] **Step 8: 사용자에게 swap 사유 받기 (HALT)**

> "Step 1 swap 적용 완료. log.md `[2026-05-10] decide` 항목의 사유를 한 줄 알려주세요. (예: 'Codex 한도 부족', 'Opus 4.7 출력 품질 우선', '사용자 선호도 변경' 등). 받으면 wiki에 기록 후 Step 1 종료."

사용자 응답 받고 다음 step.

- [ ] **Step 9: 사용자 사유를 wiki에 반영**

`roles.md`와 `log.md`의 "Reason: <사용자 결정 사유>" 자리에 사용자 입력 삽입.

- [ ] **Step 10: Commit (Step 1 종료)**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step1 done] Director swap + Immediate-Reflection 7 wiki pages"
```

---

## Step 2: Knowledge DB Phase 1

목적: Qdrant Cloud + 12 컬렉션 + Voyage-3 + 첫 인덱싱 + Wiki-First → KB-Second hook.

### Task 13: Qdrant Cloud 가입 (사용자 승인 게이트)

**Files:**
- Modify: `~/.hermes/.env`

- [ ] **Step 1: 사용자에게 Qdrant Cloud 신규 billing surface 승인 요청 (HALT)**

> "Knowledge DB는 Qdrant Cloud 신규 billing surface입니다. free tier로 시작 (1GB RAM, 4GB storage). 사용량 증가 시 ~$25/월. 승인하시면 사용자가 직접 https://cloud.qdrant.io 에서 cluster 생성 + API key 발급 후, 다음을 알려주세요:
> - QDRANT_URL (예: https://abc-xyz.us-east.aws.cloud.qdrant.io:6333)
> - QDRANT_API_KEY"

승인 + 키 받으면 다음.

- [ ] **Step 2: ~/.hermes/.env에 키 추가**

```bash
cat >> ~/.hermes/.env <<EOF
QDRANT_URL=<사용자 입력>
QDRANT_API_KEY=<사용자 입력>
EOF
chmod 600 ~/.hermes/.env
```

- [ ] **Step 3: 연결 검증**

```bash
source ~/.hermes/.env
curl -s -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections" | jq .
```

Expected: `{"result": {"collections": []}, "status": "ok", "time": ...}`.

- [ ] **Step 4: Commit (.env는 git에서 제외, 검증만)**

```bash
git status  # .env는 .gitignore에 포함되어 있어야
echo "Qdrant Cloud connected"
```

### Task 14: Voyage AI 키 + 12 컬렉션 생성

**Files:**
- Modify: `~/.hermes/.env`
- Create: `/Users/main/hermes-multi-agent-config/scripts/create_collections.py`
- Test: `/Users/main/hermes-multi-agent-config/scripts/test_create_collections.py`

- [ ] **Step 1: 사용자에게 Voyage API key 요청 (HALT)**

> "Voyage-3 임베딩(~$0.10/M tokens, ~$1-3/월 추정). https://dash.voyageai.com 에서 API key 발급 후 알려주세요."

받으면 .env에 추가:

```bash
echo "VOYAGE_API_KEY=<사용자 입력>" >> ~/.hermes/.env
```

검증:
```bash
source ~/.hermes/.env
curl -s -X POST "https://api.voyageai.com/v1/embeddings" \
  -H "Authorization: Bearer $VOYAGE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input":"test","model":"voyage-3"}' | jq '.data[0].embedding | length'
```

Expected: `1024`.

- [ ] **Step 2: Write failing test for create_collections**

```python
# scripts/test_create_collections.py
import os
import pytest
from create_collections import COLLECTIONS, build_create_request

def test_collections_count():
    assert len(COLLECTIONS) == 12

def test_collections_names():
    expected = {
        "wiki_entities", "wiki_concepts", "wiki_architecture",
        "kb_papers", "kb_oss_projects", "kb_industry_solutions",
        "kb_lessons_learned", "kb_dev_docs",
        "mythrill_code", "chat_memory", "personal_notes", "topics",
    }
    assert {c["name"] for c in COLLECTIONS} == expected

def test_build_create_request_voyage_dim():
    req = build_create_request("wiki_entities")
    assert req["vectors"]["size"] == 1024
    assert req["vectors"]["distance"] == "Cosine"

def test_topics_collection_has_no_vectors():
    # topics is metadata-only
    req = build_create_request("topics")
    assert "vectors" not in req or req.get("vectors", {}).get("size") == 0
```

- [ ] **Step 3: Run test, expect fail**

```bash
cd /Users/main/hermes-multi-agent-config/scripts
python -m pytest test_create_collections.py -v
```

Expected: ImportError.

- [ ] **Step 4: Implement create_collections.py**

```python
# scripts/create_collections.py
"""Create the 12 Qdrant collections for the Hermes Knowledge DB.

Run once during Step 2. Idempotent — skips existing collections.
"""
from __future__ import annotations
import os
import sys
import requests
from typing import Any

DIM = 1024  # voyage-3 / bge-m3 both produce 1024-dim vectors

COLLECTIONS: list[dict[str, Any]] = [
    {"name": "wiki_entities",       "kind": "vector"},
    {"name": "wiki_concepts",       "kind": "vector"},
    {"name": "wiki_architecture",   "kind": "vector"},
    {"name": "kb_papers",           "kind": "vector"},
    {"name": "kb_oss_projects",     "kind": "vector"},
    {"name": "kb_industry_solutions","kind": "vector"},
    {"name": "kb_lessons_learned",  "kind": "vector"},
    {"name": "kb_dev_docs",         "kind": "vector"},
    {"name": "mythrill_code",       "kind": "vector"},
    {"name": "chat_memory",         "kind": "vector"},
    {"name": "personal_notes",      "kind": "vector"},
    {"name": "topics",              "kind": "metadata"},  # payload-only
]


def build_create_request(name: str) -> dict[str, Any]:
    spec = next(c for c in COLLECTIONS if c["name"] == name)
    if spec["kind"] == "metadata":
        return {"vectors": {"size": 0, "distance": "Cosine"}}
    return {
        "vectors": {"size": DIM, "distance": "Cosine"},
        "hnsw_config": {"m": 16, "ef_construct": 100},
        "quantization_config": {"scalar": {"type": "int8", "always_ram": True}},
    }


def create(url: str, api_key: str, name: str) -> str:
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    # Check existence
    r = requests.get(f"{url}/collections/{name}", headers=headers)
    if r.status_code == 200:
        return "exists"
    body = build_create_request(name)
    r = requests.put(f"{url}/collections/{name}", headers=headers, json=body)
    r.raise_for_status()
    return "created"


def main() -> int:
    url = os.environ["QDRANT_URL"].rstrip("/")
    api_key = os.environ["QDRANT_API_KEY"]
    for spec in COLLECTIONS:
        status = create(url, api_key, spec["name"])
        print(f"{spec['name']:30s} {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run test, expect pass**

```bash
python -m pytest test_create_collections.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Run create_collections on real cluster**

```bash
source ~/.hermes/.env
python scripts/create_collections.py
```

Expected: 12 lines, each `created`.

검증:
```bash
curl -s -H "api-key: $QDRANT_API_KEY" "$QDRANT_URL/collections" | jq '.result.collections[].name' | sort
```

Expected: 12 컬렉션 이름.

- [ ] **Step 7: Commit**

```bash
git add scripts/create_collections.py scripts/test_create_collections.py
git commit -m "[Step2] Create 12 Qdrant collections"
```

### Task 15: `knowledge-db` toolset 구현 — kb_search, kb_upsert, dedupe

**Files:**
- Modify: `~/.hermes/skills/knowledge-db/kb_tools.py`
- Test: `~/.hermes/skills/knowledge-db/test_kb_tools.py`

- [ ] **Step 1: Write failing tests**

```python
# ~/.hermes/skills/knowledge-db/test_kb_tools.py
import pytest
from unittest.mock import patch, MagicMock
from kb_tools import compute_content_hash, validate_payload, kb_search, kb_upsert

def test_compute_content_hash_stable():
    h1 = compute_content_hash("hello world")
    h2 = compute_content_hash("hello world")
    assert h1 == h2 and h1.startswith("sha256:")

def test_validate_payload_requires_source_url():
    bad = {"content_hash": "x", "retrieved_at": "2026-05-10", "citation": "c"}
    with pytest.raises(ValueError, match="source_url"):
        validate_payload(bad)

def test_validate_payload_passes_complete():
    good = {
        "source_url": "https://arxiv.org/abs/2401.00001",
        "content_hash": "sha256:abc",
        "retrieved_at": "2026-05-10T12:00:00Z",
        "citation": "Smith 2026",
        "language": "en",
        "embedding_model": "voyage-3",
        "confidence": "high",
    }
    validate_payload(good)  # no raise

def test_kb_upsert_dedupes_on_content_hash():
    with patch("kb_tools._qdrant_get") as mock_get, patch("kb_tools._qdrant_put") as mock_put:
        mock_get.return_value = {"result": [{"id": "existing"}]}  # hash hit
        result = kb_upsert("kb_papers", text="x", payload={
            "source_url":"u","content_hash":"sha256:x","retrieved_at":"t",
            "citation":"c","language":"en","embedding_model":"voyage-3","confidence":"high",
        })
        assert result == "skipped_dedupe"
        mock_put.assert_not_called()
```

- [ ] **Step 2: Run test, expect fail**

```bash
cd ~/.hermes/skills/knowledge-db
python -m pytest test_kb_tools.py -v
```

Expected: ImportError or AttributeError.

- [ ] **Step 3: Implement kb_tools.py**

```python
# ~/.hermes/skills/knowledge-db/kb_tools.py
"""Knowledge DB CRUD with dedupe and forced provenance.

Functions: kb_search, kb_upsert, kb_topic_register, kb_topic_list, kb_stats.
All upserts validate payload (source_url + content_hash + citation + retrieved_at)
and skip on content_hash collision (dedupe).
"""
from __future__ import annotations
import hashlib
import json
import os
import requests
from datetime import datetime, timezone

REQUIRED_PAYLOAD = (
    "source_url", "content_hash", "retrieved_at", "citation",
    "language", "embedding_model", "confidence",
)


def compute_content_hash(text: str) -> str:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{h}"


def validate_payload(p: dict) -> None:
    missing = [k for k in REQUIRED_PAYLOAD if k not in p or p[k] in (None, "")]
    if missing:
        raise ValueError(f"missing required payload fields: {missing}")


def _qdrant_url() -> str:
    return os.environ["QDRANT_URL"].rstrip("/")


def _qdrant_headers() -> dict:
    return {"api-key": os.environ["QDRANT_API_KEY"], "Content-Type": "application/json"}


def _qdrant_get(path: str, params: dict | None = None) -> dict:
    r = requests.get(f"{_qdrant_url()}{path}", headers=_qdrant_headers(), params=params)
    r.raise_for_status()
    return r.json()


def _qdrant_put(path: str, body: dict) -> dict:
    r = requests.put(f"{_qdrant_url()}{path}", headers=_qdrant_headers(), json=body)
    r.raise_for_status()
    return r.json()


def _qdrant_post(path: str, body: dict) -> dict:
    r = requests.post(f"{_qdrant_url()}{path}", headers=_qdrant_headers(), json=body)
    r.raise_for_status()
    return r.json()


def _embed(text: str) -> list[float]:
    r = requests.post(
        "https://api.voyageai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {os.environ['VOYAGE_API_KEY']}", "Content-Type": "application/json"},
        json={"input": text, "model": "voyage-3"},
    )
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


def kb_search(collection: str, query: str, top_k: int = 10, filter: dict | None = None) -> list[dict]:
    vec = _embed(query)
    body = {"vector": vec, "limit": top_k, "with_payload": True}
    if filter:
        body["filter"] = filter
    res = _qdrant_post(f"/collections/{collection}/points/search", body)
    return res.get("result", [])


def kb_upsert(collection: str, text: str, payload: dict, point_id: str | None = None) -> str:
    """Upsert one point. Returns 'created' | 'updated' | 'skipped_dedupe'."""
    if "content_hash" not in payload:
        payload["content_hash"] = compute_content_hash(text)
    if "retrieved_at" not in payload:
        payload["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    if "embedding_model" not in payload:
        payload["embedding_model"] = "voyage-3"
    validate_payload(payload)

    # Dedupe: query existing points by content_hash
    scroll = _qdrant_post(f"/collections/{collection}/points/scroll", {
        "filter": {"must": [{"key": "content_hash", "match": {"value": payload["content_hash"]}}]},
        "limit": 1,
    })
    existing = scroll.get("result", {}).get("points", [])
    if existing:
        return "skipped_dedupe"

    vec = _embed(text)
    pid = point_id or payload["content_hash"].split(":", 1)[1][:32]
    body = {"points": [{"id": pid, "vector": vec, "payload": payload}]}
    _qdrant_put(f"/collections/{collection}/points", body)
    return "created"


def kb_topic_register(name: str, description: str, keywords: list[str], crawl_freq: str = "daily") -> str:
    payload = {
        "name": name,
        "description": description,
        "keywords": keywords,
        "status": "active",
        "crawl_freq": crawl_freq,
        "last_crawled": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        # Forced fields for consistency (topics are metadata-only)
        "source_url": "n/a",
        "content_hash": compute_content_hash(name),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "citation": f"topic:{name}",
        "language": "en",
        "embedding_model": "voyage-3",
        "confidence": "high",
    }
    body = {"points": [{"id": name, "vector": [], "payload": payload}]}
    _qdrant_put("/collections/topics/points", body)
    return name


def kb_topic_list(status: str = "active") -> list[dict]:
    res = _qdrant_post("/collections/topics/points/scroll", {
        "filter": {"must": [{"key": "status", "match": {"value": status}}]},
        "limit": 100,
        "with_payload": True,
    })
    return [p["payload"] for p in res.get("result", {}).get("points", [])]


def kb_stats() -> dict:
    res = _qdrant_get("/collections")
    out = {}
    for c in res.get("result", {}).get("collections", []):
        info = _qdrant_get(f"/collections/{c['name']}")
        out[c["name"]] = info.get("result", {}).get("points_count", 0)
    return out
```

- [ ] **Step 4: Run test, expect pass**

```bash
cd ~/.hermes/skills/knowledge-db
python -m pytest test_kb_tools.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Smoke test against real Qdrant**

```bash
source ~/.hermes/.env
python -c "
import sys
sys.path.insert(0, '$HOME/.hermes/skills/knowledge-db')
from kb_tools import kb_upsert, kb_search, kb_stats
res = kb_upsert('kb_papers', text='Test paper abstract', payload={
    'source_url': 'https://example.com/test',
    'citation': 'Test 2026',
    'relevance_topics': ['smoke_test'],
    'language': 'en', 'confidence': 'low',
})
print('upsert:', res)
hits = kb_search('kb_papers', 'test paper')
print('search hits:', len(hits))
print('stats:', kb_stats())
"
```

Expected: `upsert: created`, `search hits: 1`, `stats: {...}` 12 컬렉션 모두 0+ 표시.

- [ ] **Step 6: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step2] knowledge-db toolset: kb_search/upsert/topic/stats with dedupe + payload validation"
```

### Task 16: `research-external` toolset 구현 — arXiv, GitHub, Tavily

**Files:**
- Modify: `~/.hermes/skills/research-external/external_tools.py`
- Test: `~/.hermes/skills/research-external/test_external_tools.py`

- [ ] **Step 1: 사용자에게 Tavily + GitHub 토큰 요청 (HALT)**

> "research-external에 다음 키 필요:
> - TAVILY_API_KEY (https://tavily.com, ~$5-10/월)
> - GITHUB_TOKEN (https://github.com/settings/tokens, public_repo scope, 무료)
> 알려주시면 .env에 추가."

받으면:
```bash
echo "TAVILY_API_KEY=<사용자 입력>" >> ~/.hermes/.env
echo "GITHUB_TOKEN=<사용자 입력>" >> ~/.hermes/.env
chmod 600 ~/.hermes/.env
```

- [ ] **Step 2: Write failing tests**

```python
# ~/.hermes/skills/research-external/test_external_tools.py
import pytest
from unittest.mock import patch, MagicMock
from external_tools import arxiv_search, github_search, tavily_search, normalize_chunk

def test_normalize_chunk_requires_source():
    with pytest.raises(ValueError):
        normalize_chunk({"title": "T"})  # no url

def test_normalize_chunk_produces_required_fields():
    c = normalize_chunk({"title": "T", "url": "https://x", "content": "abstract", "authors": ["A"]})
    assert c["source_url"] == "https://x"
    assert "citation" in c
    assert c["language"] == "en"

def test_arxiv_search_invokes_api():
    with patch("external_tools.requests.get") as mock_get:
        mock_get.return_value.text = """<feed><entry><title>Paper</title><id>http://arxiv.org/abs/2401.00001</id><summary>abstract</summary><author><name>Smith</name></author></entry></feed>"""
        mock_get.return_value.raise_for_status = MagicMock()
        results = arxiv_search("mpm physics", max_results=1)
        assert len(results) == 1
        assert "arxiv.org" in results[0]["source_url"]
```

- [ ] **Step 3: Run test, expect fail**

```bash
cd ~/.hermes/skills/research-external
python -m pytest test_external_tools.py -v
```

- [ ] **Step 4: Implement external_tools.py**

```python
# ~/.hermes/skills/research-external/external_tools.py
"""External knowledge source search.

Functions: arxiv_search, semantic_scholar_search, github_search,
tavily_search, patent_search, archive_wayback, pdf_extract.

All results pass through normalize_chunk → source_url, citation, content_hash, etc.
Source-Enforcement: discard chunks without source URL.
"""
from __future__ import annotations
import hashlib
import os
import re
from datetime import datetime, timezone
from typing import Any
import requests
import xml.etree.ElementTree as ET


def _hash(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def normalize_chunk(raw: dict) -> dict:
    url = raw.get("url") or raw.get("source_url")
    if not url:
        raise ValueError("missing source url; Source-Enforcement violation")
    text = raw.get("content") or raw.get("abstract") or raw.get("summary") or ""
    authors = raw.get("authors", [])
    title = raw.get("title", "")
    year = raw.get("year") or _extract_year(raw)
    citation_parts = [", ".join(authors[:3])] if authors else []
    if year:
        citation_parts.append(f"({year})")
    citation_parts.append(title)
    citation_parts.append(url)
    return {
        "source_url": url,
        "content_hash": _hash(f"{title}\n{text}"),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "citation": " ".join(p for p in citation_parts if p),
        "language": raw.get("language", "en"),
        "embedding_model": "voyage-3",
        "confidence": raw.get("confidence", "medium"),
        "title": title,
        "authors": authors,
        "year": year,
        "_text": text,  # for embedding
        **{k: v for k, v in raw.items() if k not in {"url", "source_url", "content", "abstract", "summary"}},
    }


def _extract_year(raw: dict) -> int | None:
    for k in ("published", "publishedAt", "pushed_at", "created_at"):
        if v := raw.get(k):
            m = re.search(r"(\d{4})", str(v))
            if m:
                return int(m.group(1))
    return None


def arxiv_search(query: str, max_results: int = 10, since_days: int | None = None) -> list[dict]:
    base = "http://export.arxiv.org/api/query"
    q = f"all:{query}"
    if since_days:
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y%m%d")
        q = f"{q} AND submittedDate:[{since}* TO 99999999*]"
    r = requests.get(base, params={"search_query": q, "max_results": max_results})
    r.raise_for_status()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(r.text)
    out = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", "", ns) or "").strip()
        url = (entry.findtext("a:id", "", ns) or "").strip()
        summary = (entry.findtext("a:summary", "", ns) or "").strip()
        authors = [a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns)]
        published = entry.findtext("a:published", "", ns)
        out.append(normalize_chunk({
            "title": title, "url": url, "abstract": summary,
            "authors": authors, "published": published,
            "arxiv_id": url.rsplit("/", 1)[-1] if url else None,
        }))
    return out


def semantic_scholar_search(query: str, limit: int = 10) -> list[dict]:
    base = "https://api.semanticscholar.org/graph/v1/paper/search"
    r = requests.get(base, params={"query": query, "limit": limit, "fields": "title,authors,year,abstract,url,externalIds"})
    r.raise_for_status()
    out = []
    for p in r.json().get("data", []):
        out.append(normalize_chunk({
            "title": p.get("title"),
            "url": p.get("url") or f"https://www.semanticscholar.org/paper/{p.get('paperId')}",
            "abstract": p.get("abstract") or "",
            "authors": [a.get("name") for a in p.get("authors", [])],
            "year": p.get("year"),
            "doi": (p.get("externalIds") or {}).get("DOI"),
        }))
    return out


def github_search(query: str, sort: str = "stars", since_days: int | None = None, limit: int = 10) -> list[dict]:
    q = query
    if since_days:
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%d")
        q = f"{q} pushed:>={since}"
    headers = {"Accept": "application/vnd.github+json"}
    if tok := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {tok}"
    r = requests.get("https://api.github.com/search/repositories", headers=headers,
                     params={"q": q, "sort": sort, "per_page": limit})
    r.raise_for_status()
    out = []
    for repo in r.json().get("items", []):
        out.append(normalize_chunk({
            "title": repo["full_name"],
            "url": repo["html_url"],
            "content": repo.get("description") or "",
            "stars": repo.get("stargazers_count"),
            "last_commit": repo.get("pushed_at"),
            "license": (repo.get("license") or {}).get("spdx_id"),
            "language": "en",
            "status": "archived" if repo.get("archived") else "active",
        }))
    return out


def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    r = requests.post("https://api.tavily.com/search", json={
        "api_key": os.environ["TAVILY_API_KEY"],
        "query": query,
        "max_results": max_results,
    })
    r.raise_for_status()
    out = []
    for item in r.json().get("results", []):
        out.append(normalize_chunk({
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content") or "",
        }))
    return out
```

- [ ] **Step 5: Run test, expect pass**

```bash
cd ~/.hermes/skills/research-external
python -m pytest test_external_tools.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Smoke test (real APIs, 1 query each)**

```bash
source ~/.hermes/.env
python -c "
import sys
sys.path.insert(0, '$HOME/.hermes/skills/research-external')
from external_tools import arxiv_search, github_search, tavily_search
print('arxiv:', len(arxiv_search('mpm material point method', max_results=2)))
print('github:', len(github_search('material point method', limit=2)))
print('tavily:', len(tavily_search('niagara unreal vfx', max_results=2)))
"
```

Expected: 각 2 결과.

- [ ] **Step 7: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step2] research-external toolset: arxiv, semantic-scholar, github, tavily"
```

### Task 17: Wiki 인덱싱 첫 패스 (62 페이지 → 3 컬렉션)

**Files:**
- Create: `/Users/main/hermes-multi-agent-config/scripts/index_wiki.py`
- Test: `/Users/main/hermes-multi-agent-config/scripts/test_index_wiki.py`

- [ ] **Step 1: Write failing test**

```python
# scripts/test_index_wiki.py
from pathlib import Path
from index_wiki import index_page, route_collection

def test_route_entities():
    assert route_collection(Path("entities/mythrill-pipeline.md")) == "wiki_entities"

def test_route_concepts():
    assert route_collection(Path("concepts/mpm-constitutive-equation-swap.md")) == "wiki_concepts"

def test_route_architecture():
    assert route_collection(Path("architecture/roles.md")) == "wiki_architecture"

def test_route_unknown_returns_none():
    assert route_collection(Path("raw/something.md")) is None
```

- [ ] **Step 2: Run test, expect fail**

- [ ] **Step 3: Implement index_wiki.py**

```python
# scripts/index_wiki.py
"""Index the entire ~/.hermes/wiki into 3 KB collections (wiki_entities,
wiki_concepts, wiki_architecture) on first pass.

Idempotent via dedupe (content_hash). Re-runnable on wiki updates.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "knowledge-db"))
from kb_tools import kb_upsert, compute_content_hash  # type: ignore

ROUTING = {
    "entities/": "wiki_entities",
    "concepts/": "wiki_concepts",
    "architecture/": "wiki_architecture",
}

WIKI = Path.home() / ".hermes" / "wiki"


def route_collection(rel: Path) -> str | None:
    s = str(rel).replace("\\", "/")
    for prefix, coll in ROUTING.items():
        if s.startswith(prefix):
            return coll
    return None


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}
    import yaml
    fm = yaml.safe_load(text[3:end]) or {}
    return fm


def index_page(path: Path) -> str:
    rel = path.relative_to(WIKI)
    coll = route_collection(rel)
    if not coll:
        return "skipped_route"
    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    title = fm.get("title", path.stem)
    sources = fm.get("sources", [])
    payload = {
        "source_url": f"file://{path}",
        "citation": f"[[{path.stem}]] — {title}",
        "wiki_path": str(rel),
        "wiki_type": fm.get("type", "unknown"),
        "wiki_tags": fm.get("tags", []),
        "wiki_sources": sources,
        "language": "ko" if any(0xAC00 <= ord(c) <= 0xD7A3 for c in title) else "en",
        "confidence": fm.get("confidence", "medium"),
        "embedding_model": "voyage-3",
    }
    return kb_upsert(coll, text=text, payload=payload, point_id=path.stem)


def main() -> int:
    counts: dict[str, int] = {"created": 0, "skipped_dedupe": 0, "skipped_route": 0}
    for page in WIKI.rglob("*.md"):
        if "raw/" in str(page) or page.name in ("CLAUDE.md", "SCHEMA.md", "log.md", "index.md"):
            continue
        result = index_page(page)
        counts[result] = counts.get(result, 0) + 1
        print(f"  {result:20s} {page.relative_to(WIKI)}")
    print(f"\nTotals: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, expect pass**

- [ ] **Step 5: Run real indexing**

```bash
source ~/.hermes/.env
python scripts/index_wiki.py
```

Expected: ~57 페이지 (entities 31 + concepts 26 + architecture 5, 일부 raw 제외) `created`. Re-run 시 모두 `skipped_dedupe`.

검증:
```bash
python -c "
import sys
sys.path.insert(0, '$HOME/.hermes/skills/knowledge-db')
from kb_tools import kb_stats
print(kb_stats())
"
```

Expected: `wiki_entities: ~31`, `wiki_concepts: ~26`, `wiki_architecture: ~5`.

- [ ] **Step 6: Commit**

```bash
git add scripts/index_wiki.py scripts/test_index_wiki.py
git commit -m "[Step2] First-pass index of 62 wiki pages into 3 collections"
```

### Task 18: mythrill-pipeline/src/ 인덱싱 + Wiki-First → KB-Second hook

**Files:**
- Create: `/Users/main/hermes-multi-agent-config/scripts/index_mythrill.py`
- Create: `~/.hermes/patches/wiki_first_kb_second.py`

- [ ] **Step 1: index_mythrill.py 작성**

```python
# scripts/index_mythrill.py
"""Index mythrill-pipeline/src/ into mythrill_code collection.

One chunk per .py file (small files) or per top-level def/class (large files).
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "knowledge-db"))
from kb_tools import kb_upsert  # type: ignore

ROOT = Path.home() / "mythrill-pipeline" / "src"


def main() -> int:
    counts: dict[str, int] = {}
    for py in ROOT.rglob("*.py"):
        if "__pycache__" in str(py) or "venv" in str(py):
            continue
        text = py.read_text(encoding="utf-8")
        rel = py.relative_to(ROOT.parent)
        result = kb_upsert("mythrill_code", text=text, payload={
            "source_url": f"file://{py}",
            "citation": f"mythrill:{rel}",
            "file_path": str(rel),
            "language": "en",
            "confidence": "high",
            "embedding_model": "voyage-3",
            "module": str(rel.parent),
        }, point_id=str(rel).replace("/", "_").replace(".", "_"))
        counts[result] = counts.get(result, 0) + 1
        print(f"  {result:20s} {rel}")
    print(f"\nTotals: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: 실행**

```bash
source ~/.hermes/.env
python scripts/index_mythrill.py
```

Expected: src/ 안 .py 파일 모두 `created`.

- [ ] **Step 3: Wiki-First → KB-Second hook 패치**

```python
# ~/.hermes/patches/wiki_first_kb_second.py
"""Wiki-First → KB-Second search hook.

Hooks into orchestrator's Wiki-First search routine. When the in-memory wiki
graph traversal returns < THRESHOLD relevance, fall through to KB search across
wiki_* collections, then kb_* collections.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "knowledge-db"))
from kb_tools import kb_search  # type: ignore

THRESHOLD = 0.5  # below: fall through to KB
WIKI_COLLECTIONS = ("wiki_architecture", "wiki_entities", "wiki_concepts")
KB_COLLECTIONS = ("kb_papers", "kb_oss_projects", "kb_dev_docs", "kb_industry_solutions", "kb_lessons_learned")


def search(query: str, top_k: int = 8) -> list[dict]:
    """Two-tier search. Returns chunks with source_url + citation."""
    hits: list[dict] = []
    for coll in WIKI_COLLECTIONS:
        try:
            res = kb_search(coll, query, top_k=top_k // 2)
        except Exception:
            continue
        for r in res:
            score = r.get("score", 0.0)
            if score >= THRESHOLD:
                hits.append({"collection": coll, "score": score, "payload": r["payload"]})
    if hits:
        return sorted(hits, key=lambda h: h["score"], reverse=True)[:top_k]

    # Wiki miss → KB
    for coll in KB_COLLECTIONS:
        try:
            res = kb_search(coll, query, top_k=top_k // 2)
        except Exception:
            continue
        for r in res:
            hits.append({"collection": coll, "score": r.get("score", 0.0), "payload": r["payload"]})
    return sorted(hits, key=lambda h: h["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    import json
    q = " ".join(sys.argv[1:]) or "mpm constitutive equation"
    print(json.dumps(search(q), indent=2, ensure_ascii=False)[:2000])
```

- [ ] **Step 4: 검증 (smoke search)**

```bash
source ~/.hermes/.env
python ~/.hermes/patches/wiki_first_kb_second.py "mythrill VFX pipeline"
```

Expected: top hits에 mythrill-architecture entity·concept 페이지 등장.

- [ ] **Step 5: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step2] Index mythrill src + Wiki-First→KB-Second hook"
```

### Task 19: Step 2 완료 — wiki Immediate-Reflection

**Files:**
- Create: `~/.hermes/wiki/architecture/knowledge-db.md`
- Create: `~/.hermes/wiki/entities/qdrant-instance.md`
- Create: `~/.hermes/wiki/concepts/wiki-token-cost-reduction.md`
- Modify: `~/.hermes/wiki/log.md`, `index.md`

- [ ] **Step 1: architecture/knowledge-db.md 작성**

```bash
cat > ~/.hermes/wiki/architecture/knowledge-db.md <<'EOF'
---
title: Knowledge DB — Qdrant-backed semantic search index
created: 2026-05-10
updated: 2026-05-10
type: architecture
tags: [knowledge-db, qdrant, rag, multi-agent]
sources: ["docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md"]
confidence: high
---

# Knowledge DB

A Qdrant-backed semantic index over wiki + external knowledge. Primary purpose: reduce token cost when traversing wiki at LLM call time. Secondary: persist external research with forced provenance and dedupe.

## Two-Tier Search (Wiki-First → KB-Second)

See `~/.hermes/patches/wiki_first_kb_second.py`. Wiki page graph traversal first; on miss fall through to `wiki_*` collections, then `kb_*` collections.

## Collections (12)

wiki_entities · wiki_concepts · wiki_architecture · kb_papers · kb_oss_projects · kb_industry_solutions · kb_lessons_learned · kb_dev_docs · mythrill_code · chat_memory · personal_notes · topics.

## Forced Payload (every chunk)

`source_url`, `content_hash` (sha256 dedupe key), `retrieved_at` (ISO8601), `citation` (markdown), `relevance_topics`, `language`, `embedding_model`, `confidence`. Validation enforced in `kb_tools.kb_upsert`.

## Embedding

Phase 1: Voyage-3 (1024 dim). Phase 2: BGE-M3 (1024 dim, local). Same dim → schema unchanged on swap.

## Related

[[continuous-research-loop]] · [[qdrant-instance]] · [[wiki-token-cost-reduction]] · [[orchestrator-protocol]] · [[multi-agent-system]]
EOF
```

- [ ] **Step 2: entities/qdrant-instance.md, concepts/wiki-token-cost-reduction.md 작성**

(spec §9 표준 frontmatter, 내용은 spec §6, §11 인용)

- [ ] **Step 3: log.md 항목 추가**

```bash
cat >> ~/.hermes/wiki/log.md <<'EOF'

## [2026-05-10] create | Knowledge DB Phase 1 (Qdrant Cloud + 12 collections)
- 신규: Qdrant Cloud cluster, 12 컬렉션 생성, Voyage-3 임베딩.
- 신규 toolset: knowledge-db (kb_search/upsert/topic/stats), research-external (arxiv/scholar/github/tavily).
- 인덱싱: wiki 62 페이지 → wiki_{entities,concepts,architecture}. mythrill-pipeline/src/ → mythrill_code.
- 신규 hook: ~/.hermes/patches/wiki_first_kb_second.py.
- 검증: kb_stats() 모든 컬렉션 응답, smoke search hit.
- 비용: Qdrant free tier ($0). Voyage usage ~$1/월 추정.
EOF
```

- [ ] **Step 4: index.md updated 갱신, 신규 페이지 항목 추가**

- [ ] **Step 5: 사용자 보고**

> "Step 2 완료. KB 12 컬렉션 가동. wiki 62 + mythrill src 인덱싱. Wiki-First→KB-Second hook 활성. Step 3 cron + Topic Tracker 진행해도 될까?"

- [ ] **Step 6: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step2 done] KB Phase 1 + 3 new wiki pages + Immediate-Reflection"
```

---

## Step 3: Continuous Researcher cron + Topic Tracker

목적: cron 4종 등록, Topic Tracker 자동 추천 + 사용자 승인 흐름, R&D A·B의 cron 모드 가동.

### Task 20: Hermes cron 4종 등록 (`~/.hermes/cron/jobs.json`)

**Files:**
- Modify: `~/.hermes/cron/jobs.json`

- [ ] **Step 1: 현재 jobs.json 확인**

```bash
jq '.' ~/.hermes/cron/jobs.json
```

- [ ] **Step 2: cron 4종 추가**

```bash
python <<'EOF'
import json
from pathlib import Path

p = Path.home() / ".hermes" / "cron" / "jobs.json"
data = json.loads(p.read_text())
existing = {j["name"] for j in data.get("jobs", [])}

new_jobs = [
    {"name": "topic_crawl_daily",
     "schedule": "0 3 * * *",
     "command": "hermes researcher crawl --mode daily",
     "description": "Daily crawl: arxiv/github/HN for active topics. Source-Enforcement + dedupe."},
    {"name": "topic_crawl_weekly",
     "schedule": "0 4 * * 0",
     "command": "hermes researcher crawl --mode weekly",
     "description": "Weekly broad crawl: patent/wayback/awesome lists. oss_projects status refresh."},
    {"name": "topic_curation_weekly",
     "schedule": "0 5 * * 6",
     "command": "hermes researcher curate-topics",
     "description": "Director reviews topics: noise/merge/rename candidates → Telegram card → user approval."},
    {"name": "cost_report_weekly",
     "schedule": "0 18 * * 0",
     "command": "hermes report cost --period 7d --notify telegram",
     "description": "Weekly token + KB stats report to Telegram + log.md."},
]
for j in new_jobs:
    if j["name"] not in existing:
        data.setdefault("jobs", []).append(j)
p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
print("jobs:", [j["name"] for j in data["jobs"]])
EOF
```

- [ ] **Step 3: hermes cron list로 검증**

```bash
hermes cron list
```

Expected: 4 신규 job 출력.

- [ ] **Step 4: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step3] Register 4 cron jobs (daily/weekly crawl + curation + cost report)"
```

### Task 21: `hermes researcher crawl` 명령 구현

**Files:**
- Create: `~/.hermes/skills/research-external/crawl_loop.py`

- [ ] **Step 1: crawl_loop.py 작성 (영어, AI-to-AI 원칙)**

```python
# ~/.hermes/skills/research-external/crawl_loop.py
"""Continuous Researcher cron loop.

Invoked by:
  hermes researcher crawl --mode daily
  hermes researcher crawl --mode weekly

For each active topic, query external sources, normalize, dedupe-upsert into
KB. Append a one-line summary to ~/.hermes/wiki/log.md (Korean OK).
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "knowledge-db"))
sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "research-external"))

from kb_tools import kb_topic_list, kb_upsert  # type: ignore
from external_tools import (  # type: ignore
    arxiv_search, github_search, semantic_scholar_search, tavily_search,
)

DAILY_SOURCES = (
    ("arxiv", arxiv_search, {"since_days": 1}),
    ("github", github_search, {"since_days": 1}),
)
WEEKLY_SOURCES = (
    ("arxiv", arxiv_search, {"since_days": 7}),
    ("semantic_scholar", semantic_scholar_search, {}),
    ("github", github_search, {"since_days": 7}),
    ("tavily", tavily_search, {}),
)
COLLECTION_BY_SOURCE = {
    "arxiv": "kb_papers",
    "semantic_scholar": "kb_papers",
    "github": "kb_oss_projects",
    "tavily": "kb_dev_docs",
}


def crawl_one_topic(topic: dict, sources) -> dict[str, int]:
    counts = {"created": 0, "skipped_dedupe": 0, "errors": 0}
    keywords = topic.get("keywords") or [topic["name"]]
    query = " ".join(keywords[:3])
    for src_name, fn, kwargs in sources:
        coll = COLLECTION_BY_SOURCE[src_name]
        try:
            chunks = fn(query, **{**kwargs, **({"max_results": 5} if "max_results" in fn.__code__.co_varnames else {})})
        except Exception as e:
            counts["errors"] += 1
            print(f"  [{src_name}] error: {e}", file=sys.stderr)
            continue
        for c in chunks:
            text = c.pop("_text", "") or c.get("title", "")
            payload = {**c, "relevance_topics": [topic["name"]]}
            try:
                result = kb_upsert(coll, text=text, payload=payload)
                counts[result] = counts.get(result, 0) + 1
            except Exception as e:
                counts["errors"] += 1
                print(f"  [{src_name}] upsert error: {e}", file=sys.stderr)
    return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["daily", "weekly"], required=True)
    args = ap.parse_args()
    sources = DAILY_SOURCES if args.mode == "daily" else WEEKLY_SOURCES

    topics = kb_topic_list(status="active")
    if not topics:
        print("No active topics. Register topics first via Topic Tracker.")
        return 0

    total = {"created": 0, "skipped_dedupe": 0, "errors": 0}
    per_topic = []
    for t in topics:
        counts = crawl_one_topic(t, sources)
        per_topic.append((t["name"], counts))
        for k, v in counts.items():
            total[k] = total.get(k, 0) + v

    # Append log line (Korean OK)
    log = Path.home() / ".hermes" / "wiki" / "log.md"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    line = f"\n## [{today}] crawl | mode={args.mode} | "
    line += " · ".join(f"{n}: +{c['created']}/dup{c['skipped_dedupe']}" for n, c in per_topic)
    line += f" | total +{total['created']} new"
    with log.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)
    return 0 if total["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: hermes 명령 wrapper 등록**

`hermes researcher crawl --mode <X>`이 `python ~/.hermes/skills/research-external/crawl_loop.py --mode <X>`를 호출하도록 설정. 정확한 위치는 hermes 버전마다 다름:

```bash
# Option A: hermes-cli alias (권장)
mkdir -p ~/.hermes/aliases
cat > ~/.hermes/aliases/researcher_crawl.yaml <<'EOF'
name: researcher_crawl
command: ["python", "/Users/main/.hermes/skills/research-external/crawl_loop.py"]
trigger: "hermes researcher crawl"
EOF

# Option B: 단순 shell wrapper
cat > ~/.hermes/bin/hermes-researcher <<'EOF'
#!/usr/bin/env bash
case "$1" in
  crawl)
    shift
    python ~/.hermes/skills/research-external/crawl_loop.py "$@"
    ;;
  curate-topics)
    python ~/.hermes/skills/research-external/curate_topics.py "$@"
    ;;
  *)
    echo "usage: hermes-researcher {crawl|curate-topics}"; exit 2;;
esac
EOF
chmod +x ~/.hermes/bin/hermes-researcher
```

cron job command를 `hermes-researcher crawl --mode daily`로 변경하거나, `hermes-cli`를 통해 alias 호출.

- [ ] **Step 3: dry run (active topic 없으면 0건 정상)**

```bash
source ~/.hermes/.env
python ~/.hermes/skills/research-external/crawl_loop.py --mode daily
```

Expected: `No active topics.` (Topic Tracker 미설정 단계).

- [ ] **Step 4: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step3] crawl_loop.py + hermes-researcher wrapper"
```

### Task 22: Topic Tracker — 자동 추천 + 사용자 승인

**Files:**
- Create: `~/.hermes/skills/research-external/topic_recommender.py`
- Create: `~/.hermes/skills/research-external/curate_topics.py`

- [ ] **Step 1: topic_recommender.py 작성**

```python
# ~/.hermes/skills/research-external/topic_recommender.py
"""Topic Tracker — extract candidate topics from mythrill code, wiki tags,
and recent chat sessions, then propose to user for approval.
"""
from __future__ import annotations
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import yaml

WIKI = Path.home() / ".hermes" / "wiki"
MYTHRILL_SRC = Path.home() / "mythrill-pipeline" / "src"


def from_wiki_tags() -> Counter:
    c: Counter = Counter()
    for page in (WIKI / "concepts").glob("*.md"):
        text = page.read_text(encoding="utf-8")
        if text.startswith("---"):
            try:
                fm = yaml.safe_load(text.split("---", 2)[1]) or {}
                for tag in fm.get("tags", []) or []:
                    c[tag] += 1
            except Exception:
                pass
    for page in (WIKI / "entities").glob("*.md"):
        text = page.read_text(encoding="utf-8")
        if text.startswith("---"):
            try:
                fm = yaml.safe_load(text.split("---", 2)[1]) or {}
                for tag in fm.get("tags", []) or []:
                    c[tag] += 1
            except Exception:
                pass
    return c


def from_mythrill_modules() -> Counter:
    c: Counter = Counter()
    for d in MYTHRILL_SRC.iterdir():
        if d.is_dir() and not d.name.startswith("__"):
            c[f"mythrill_{d.name}"] += 1
    return c


def recommend(top_n: int = 12) -> list[dict]:
    tags = from_wiki_tags()
    modules = from_mythrill_modules()
    merged = tags + modules
    out = []
    for name, count in merged.most_common(top_n):
        out.append({
            "name": name,
            "score": count,
            "keywords": [name.replace("_", " ")],
            "source": "wiki_tags" if name in tags else "mythrill_module",
        })
    return out


def main() -> int:
    import json
    candidates = recommend()
    print(json.dumps(candidates, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: curate_topics.py — 사용자 승인 카드 생성**

```python
# ~/.hermes/skills/research-external/curate_topics.py
"""Generate Telegram-formatted topic approval card. User responds with
'approve <name>' / 'reject <name>' / 'rename <name> <newname>' messages.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import topic_recommender


def main() -> int:
    candidates = topic_recommender.recommend(top_n=12)
    out_path = Path.home() / ".hermes" / "cron" / "output" / "topic_curation_card.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Topic Curation Card", "", "추천 토픽. Telegram에 답장으로 결정:", ""]
    for c in candidates:
        lines.append(f"- **{c['name']}** (score={c['score']}, src={c['source']}, keywords={c['keywords']})")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: 첫 추천 실행**

```bash
python ~/.hermes/skills/research-external/topic_recommender.py
```

Expected: 12개 후보 출력.

- [ ] **Step 4: 사용자 승인 흐름 (HALT)**

> "Topic Tracker 추천 12개:
> [목록]
> 등록할 토픽 이름을 콤마로 알려주세요 (예: 'mpm_constitutive_swap, taichi_mpm, niagara_vfx')."

받으면:

```bash
python -c "
import sys
sys.path.insert(0, '$HOME/.hermes/skills/knowledge-db')
sys.path.insert(0, '$HOME/.hermes/skills/research-external')
from kb_tools import kb_topic_register
import topic_recommender
approved = '<사용자 입력>'.split(',')
candidates = {c['name']: c for c in topic_recommender.recommend()}
for name in approved:
    name = name.strip()
    if name in candidates:
        c = candidates[name]
        kb_topic_register(name=c['name'], description=f\"auto: {c['source']}\", keywords=c['keywords'])
        print(f'registered: {name}')
"
```

- [ ] **Step 5: 첫 daily 실행 (등록 토픽 대상)**

```bash
python ~/.hermes/skills/research-external/crawl_loop.py --mode daily
```

Expected: log.md에 `[2026-05-10] crawl | mode=daily | <topic1>: +N/dup0 ...` 항목 추가.

- [ ] **Step 6: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step3] Topic Tracker recommender + curation + first daily crawl"
```

### Task 23: R&D A·B SOUL.md cron mode 추가

**Files:**
- Modify: `~/.hermes/profiles/researcher/SOUL.md`

- [ ] **Step 1: SOUL.md 영어 cron mode 추가**

`~/.hermes/profiles/researcher/SOUL.md` 끝에 다음 섹션 추가:

```markdown

## Cron Mode (added 2026-05-10)

When invoked via `hermes researcher crawl --mode {daily|weekly}` (cron jobs `topic_crawl_daily`, `topic_crawl_weekly`):

1. Read `topics` collection (active only) via knowledge-db toolset.
2. For each topic, call research-external functions per the daily/weekly source list.
3. Apply Source-Enforcement (every chunk MUST carry source_url, citation, content_hash).
4. Apply dedupe via content_hash (skip on collision).
5. Upsert to the appropriate kb_* collection (kb_papers / kb_oss_projects / kb_dev_docs).
6. Append one log line to `~/.hermes/wiki/log.md` (Korean OK):
   `## [YYYY-MM-DD] crawl | mode={daily|weekly} | <topic>: +N/dupM ... | total +K new`

Forbidden in cron mode:
- Direct API path switches (use hermes-managed credentials only).
- Modifying wiki content (read-only). Only orchestrator commits writes.
- Korean in worker-facing output. JSON or English markdown only.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step3] researcher SOUL.md cron mode addition"
```

### Task 24: cron dry-run + 검증

- [ ] **Step 1: hermes cron 시뮬 (다음 실행 시점 확인)**

```bash
hermes cron list --next
```

Expected: 4 신규 job 모두 다음 실행 시점 표시.

- [ ] **Step 2: weekly dry-run**

```bash
python ~/.hermes/skills/research-external/crawl_loop.py --mode weekly
```

Expected: arxiv·semantic-scholar·github·tavily 4개 source × 등록 토픽 수만큼 호출. log.md 항목 추가.

- [ ] **Step 3: KB stats 확인**

```bash
python -c "
import sys; sys.path.insert(0, '$HOME/.hermes/skills/knowledge-db')
from kb_tools import kb_stats
print(kb_stats())
"
```

Expected: `kb_papers`, `kb_oss_projects`, `kb_dev_docs` 0+. `topics` = 등록 수.

- [ ] **Step 4: Commit (Step 3 종료 검증)**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step3] cron dry-run validated, first crawl ingested"
```

### Task 25: Step 3 wiki Immediate-Reflection

**Files:**
- Create: `~/.hermes/wiki/architecture/continuous-research-loop.md`
- Modify: `~/.hermes/wiki/log.md`, `index.md`

- [ ] **Step 1: continuous-research-loop.md 작성**

```bash
cat > ~/.hermes/wiki/architecture/continuous-research-loop.md <<'EOF'
---
title: Continuous Research Loop — cron-based knowledge accumulation
created: 2026-05-10
updated: 2026-05-10
type: architecture
tags: [continuous-research, cron, multi-agent, knowledge-db]
sources: ["docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md"]
confidence: high
---

# Continuous Research Loop

R&D Engineer A·B (`researcher` profile) operate in two modes: reactive (on-demand from Director) and cron (background accumulation). Cron mode adds proactive knowledge growth without user prompting.

## Cron Jobs (4)

- `topic_crawl_daily` (03:00) — arxiv/github/HN since=1d
- `topic_crawl_weekly` (Sunday 04:00) — broad: semantic-scholar/patent/wayback
- `topic_curation_weekly` (Saturday 05:00) — Director reviews topics → user approval card
- `cost_report_weekly` (Sunday 18:00) — token/KB stats Telegram report

## Source-Enforcement

Every cron-produced chunk passes through `kb_tools.validate_payload`. Missing source_url → discarded. Duplicate content_hash → skipped (idempotent re-runs).

## Topic Lifecycle

Auto-recommend (from wiki tags + mythrill modules + chat memory) → user approves → `topics` collection (status=active) → cron picks up → continuous accumulation. Weekly curation may propose archive/merge/rename.

## Related

[[knowledge-db]] · [[orchestrator-protocol]] · [[multi-agent-system]] · [[roles]]
EOF
```

- [ ] **Step 2: log.md 항목 + index.md updated**

```bash
cat >> ~/.hermes/wiki/log.md <<'EOF'

## [2026-05-10] activate | Continuous Researcher cron loop
- 신규: 4 cron job (topic_crawl_daily/weekly, topic_curation_weekly, cost_report_weekly).
- 신규: ~/.hermes/skills/research-external/{crawl_loop, topic_recommender, curate_topics}.py
- 신규: ~/.hermes/bin/hermes-researcher wrapper.
- 신규 wiki: architecture/continuous-research-loop.md.
- researcher profile SOUL.md에 cron mode 섹션 추가.
- Topic Tracker 첫 추천 → 사용자 승인 N개 → topics 컬렉션 등록 → 첫 daily crawl 성공.
EOF
```

- [ ] **Step 3: 사용자 보고**

> "Step 3 완료. cron 4종 가동. Topic Tracker 추천 + 사용자 승인 흐름 가동. 첫 daily crawl 성공. Step 4 wiki 압축 + graphify 진행해도 될까?"

- [ ] **Step 4: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step3 done] Continuous Researcher loop + 1 new wiki page + log"
```

---

## Step 4: Wiki 압축 + graphify 재실행

목적: Step 0 사용자 승인 압축 대상에 dense form 적용. raw/ 아카이브. graphify 재실행. KB 재임베딩.

### Task 26: 압축 스크립트 작성

**Files:**
- Create: `/Users/main/hermes-multi-agent-config/scripts/compress_wiki.py`
- Test: `/Users/main/hermes-multi-agent-config/scripts/test_compress_wiki.py`

- [ ] **Step 1: Write failing test**

```python
# scripts/test_compress_wiki.py
from pathlib import Path
from compress_wiki import compress_page

def test_compress_keeps_frontmatter(tmp_path):
    src = tmp_path / "page.md"
    src.write_text("---\ntitle: Test\nupdated: 2026-04-01\n---\n# Body\n\nlong content " * 200)
    out = compress_page(src, content=src.read_text())
    assert out.startswith("---\n")
    assert "title: Test" in out
    assert "updated: 2026-05-10" in out  # bumped
    assert "[원본 보존:" in out  # original link

def test_compress_extracts_summary(tmp_path):
    text = "# Hdr\n\nFirst para is the summary.\n\nMore detail.\n"
    out = compress_page(tmp_path / "p.md", content=text)
    assert "First para is the summary" in out
```

- [ ] **Step 2: Run test, expect fail**

- [ ] **Step 3: Implement compress_wiki.py**

```python
# scripts/compress_wiki.py
"""Wiki page compression — convert verbose pages to dense form (header table +
5-line key findings + raw archive link). User-approved targets only.
"""
from __future__ import annotations
import json
import re
from datetime import date
from pathlib import Path
import shutil

import yaml

WIKI = Path.home() / ".hermes" / "wiki"
RAW_ARCHIVE = WIKI / "raw" / "compressed_2026-05-10"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    fm = yaml.safe_load(text[3:end]) or {}
    body = text[end + 3:].lstrip()
    return fm, body


def first_paragraph(body: str) -> str:
    parts = re.split(r"\n\s*\n", body.strip(), maxsplit=2)
    return parts[0] if parts else ""


def compress_page(path: Path, content: str | None = None) -> str:
    text = content if content is not None else path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    fm["updated"] = "2026-05-10"
    fm.setdefault("compressed", True)
    summary = first_paragraph(body)[:1500]
    archive_rel = f"raw/compressed_2026-05-10/{path.name}"
    new_body = (
        f"# {fm.get('title', path.stem)}\n\n"
        f"> Compressed 2026-05-10. Original at [[{archive_rel}]].\n\n"
        f"## Summary\n\n{summary}\n\n"
        f"## 원본 보존\n\n[원본 보존: {archive_rel}](../{archive_rel})\n"
    )
    fm_str = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm_str}\n---\n\n{new_body}"


def main() -> int:
    final = json.loads((Path.home() / "hermes-multi-agent-config" / "docs" / "superpowers" / "audit-2026-05-10-final.json").read_text())
    targets = final["compress_targets"]
    RAW_ARCHIVE.mkdir(parents=True, exist_ok=True)
    n = 0
    for rel in targets:
        path = WIKI / rel
        if not path.exists():
            print(f"  missing: {rel}")
            continue
        # Archive original
        shutil.copy2(path, RAW_ARCHIVE / path.name)
        # Compress in place
        path.write_text(compress_page(path), encoding="utf-8")
        n += 1
        print(f"  compressed: {rel}")
    print(f"\nCompressed {n} pages → {RAW_ARCHIVE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test, expect pass**

- [ ] **Step 5: 실제 압축 실행**

```bash
cd /Users/main/hermes-multi-agent-config
python scripts/compress_wiki.py
```

Expected: 사용자 승인된 N개 페이지 압축. raw/compressed_2026-05-10/에 원본 보존.

- [ ] **Step 6: Commit**

```bash
git add scripts/compress_wiki.py scripts/test_compress_wiki.py
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step4] Compress N user-approved wiki pages + raw/ archive"
```

### Task 27: graphify 재실행

- [ ] **Step 1: graphify check-update**

```bash
graphify check-update wiki
```

Expected: pending markdown changes 감지.

- [ ] **Step 2: 로컬 cluster-only 갱신**

```bash
graphify cluster-only wiki --no-viz
```

Expected: nodes/edges/communities 갱신 보고.

- [ ] **Step 3: 사용자 승인 후 LLM semantic update (Opus quota check)**

```bash
bash ~/.hermes/bin/quota.sh
# GREEN(<50%) 일 때만 진행. 아니면 quota reset 후로 미루고 사용자에게 보고.
```

GREEN이면:

```bash
graphify wiki --update
```

Expected: LLM semantic extraction 완료, GRAPH_REPORT.md 갱신.

- [ ] **Step 4: KB 재임베딩 (압축된 wiki 페이지)**

```bash
source ~/.hermes/.env
python /Users/main/hermes-multi-agent-config/scripts/index_wiki.py
```

압축된 페이지의 content_hash가 변경됐으므로 dedupe miss → 새 청크 upsert. 이전 점들은 manual 삭제 또는 다음 갱신 시점에 정리.

- [ ] **Step 5: Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step4] graphify re-run + KB re-embed compressed pages"
```

### Task 28: Step 4 완료 — 최종 wiki Immediate-Reflection + 사용자 보고

**Files:**
- Create: `~/.hermes/wiki/concepts/setting-rebuild-2026-05-10.md`
- Modify: `~/.hermes/wiki/log.md`, `index.md`

- [ ] **Step 1: setting-rebuild-2026-05-10.md 작성 (이번 재구축 기록)**

```bash
cat > ~/.hermes/wiki/concepts/setting-rebuild-2026-05-10.md <<'EOF'
---
title: 설정 재구축 — 2026-05-10
created: 2026-05-10
updated: 2026-05-10
type: concept
tags: [rebuild, knowledge-db, multi-agent, audit]
sources: ["docs/superpowers/specs/2026-05-10-hermes-rebuild-and-knowledge-db-design.md", "docs/superpowers/plans/2026-05-10-hermes-rebuild-and-knowledge-db.md"]
confidence: high
---

# 설정 재구축 (2026-05-10)

Hermes 운영 시스템의 무에서 유 재구축 + Knowledge DB 신설 + Continuous Researcher 가동의 의사결정 기록.

## 두 layer

- **지식 (wiki content)**: 보존 + 압축. 폐기 X.
- **설정 (config·profiles·auth·toolsets·cron·patches)**: 무에서 유.

## 주요 변경

1. Director ↔ Sub-Director re-swap (Opus 4.7 ↔ GPT-5.5). OAuth-only.
2. Knowledge DB 신설 — Qdrant Cloud + 12 컬렉션 + Voyage-3.
3. Continuous Researcher cron 4종 — daily/weekly crawl + curation + cost report.
4. Wiki 압축 — N개 페이지 dense form + raw/ 아카이브.
5. graphify 재실행.

## Related

[[knowledge-db]] · [[continuous-research-loop]] · [[multi-agent-system]] · [[orchestrator-protocol]]
EOF
```

- [ ] **Step 2: log.md 최종 항목**

```bash
cat >> ~/.hermes/wiki/log.md <<'EOF'

## [2026-05-10] complete | Hermes rebuild + Knowledge DB + Continuous Researcher
- Step 0~4 완료 (audit / 설정 재구축 + Director swap / KB Phase 1 / continuous researcher / 압축 + graphify).
- 신규 wiki: knowledge-db, continuous-research-loop, qdrant-instance, wiki-token-cost-reduction, setting-rebuild-2026-05-10.
- 검증: smoke test 7종, KB 12 컬렉션 stats, cron 4종 dry-run, 첫 daily crawl 성공.
- 다음: cost_report_weekly 첫 실행으로 토큰 절감 정량 측정 시작.
EOF
```

- [ ] **Step 3: index.md updated + 신규 페이지 항목 추가**

```bash
sed -i '' 's/Last updated: .*/Last updated: 2026-05-10 | Total pages: 67/' ~/.hermes/wiki/index.md
# 신규 5 페이지 항목 추가 (수동 또는 graphify 자동)
```

- [ ] **Step 4: 사용자 보고 (최종)**

> "Step 0~4 모두 완료. Hermes 운영 시스템 재구축 + Knowledge DB 가동 + Continuous Researcher cron 4종 활성. 새 wiki 페이지 5개. 다음 일요일 18:00 첫 cost_report로 토큰 절감 효과 정량 측정 시작."

- [ ] **Step 5: 최종 Commit**

```bash
cd /Users/main/hermes-multi-agent-config && bash sync.sh
git add . && git commit -m "[Step4 done] Final wiki Immediate-Reflection — rebuild complete"
git log --oneline | head -10
```

Expected: 5 step별 commit 약 30개.

---

## 최종 검증 체크리스트

모든 Step 완료 후 다음 확인:

- [ ] **smoke test 7종**: orchestrator/sub-director/researcher A·B/tech-artist/dev-gemma 모두 `say ok` 응답
- [ ] **auth.json**: API key 0건 (`grep -r "sk-ant-api\|sk-OAI" ~/.hermes/auth.json ~/.hermes/.env` → empty)
- [ ] **KB stats**: 12 컬렉션 모두 응답, wiki_* 3 컬렉션 점수 합 ≥ 57
- [ ] **cron 4종**: `hermes cron list` 표시, 다음 실행 시점 명시
- [ ] **wiki Immediate-Reflection**: log.md 5개 항목 (`[2026-05-10]`), updated 갱신, 신규 5 페이지
- [ ] **bypass 패치**: `[anthropic_billing_bypass] Bypass installed` 로그 확인
- [ ] **사용자 보고**: 5단계 완료 보고 모두 전달

---

## Plan Self-Review

본 plan은 spec `2026-05-10-hermes-rebuild-and-knowledge-db-design.md`의 5 step과 1:1 대응한다. spec §3~§14의 모든 요구사항이 task로 구현됨을 확인:

- §3 audit → Task 1~4
- §4 architecture → Task 5~9, 11
- §5 Director swap 8단계 → Task 5, 6, 7, 8 + 12
- §6 Knowledge DB → Task 13~18
- §7 Continuous Researcher → Task 20~25
- §8 wiki 압축 → Task 26~28
- §9 신규 wiki 페이지 → Task 19, 25, 28
- §10 wiki maintenance loop → 모든 task 끝의 Immediate-Reflection 4종
- §11 비용 추정 → Pre-flight quota + cost_report_weekly cron
- §12 도입 단계 → 5 step 구조
- §13 위험·미결 → Task 12 Step 8 사용자 사유 게이트
- §14 성공 기준 → 최종 검증 체크리스트

Type/method consistency 확인:
- `kb_upsert(collection, text, payload, point_id?)` — Task 15에서 정의, Task 17·18·21·22에서 동일 시그니처 호출 ✓
- `kb_search(collection, query, top_k, filter?)` — 동일 시그니처 ✓
- `compute_content_hash(text) → "sha256:..."` ✓
- `normalize_chunk(raw) → dict` (research-external) — Task 16에서 정의, Task 21에서 호출 (실제로는 source 함수가 normalize 호출, 합 일관) ✓

Placeholder scan: "TBD"·"TODO"·"implement later" 없음. Task 12 Step 8의 swap 사유는 사용자 입력 게이트 (의도적 HALT). Task 13/14의 사용자 키 입력도 동일.

---

## Execution Handoff

Plan 작성·커밋 완료. 두 가지 실행 옵션:

**1. Subagent-Driven (recommended)** — task별로 fresh subagent 분배, 각 task 완료 후 리뷰. 빠른 반복.

**2. Inline Execution** — 본 세션에서 batch 실행. checkpoint마다 사용자 승인.

본 plan은 사용자 입력 게이트(Task 2 audit 검토, Task 12 swap 사유, Task 13 Qdrant 키, Task 14 Voyage 키, Task 16 Tavily/GitHub 키, Task 22 토픽 승인 등)가 다수라 **Inline Execution + 게이트마다 HALT**가 자연스럽습니다. 그러나 Subagent-Driven으로도 가능 (게이트에서 부모 세션이 사용자 응답 수령).

어느 쪽으로 진행할까요?

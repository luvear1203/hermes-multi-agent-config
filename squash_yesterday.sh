#!/bin/bash
# Hermes Multi-Agent Config — Daily [auto-sync] squash
# 어제 날짜의 [auto-sync] commit들을 1개로 squash 후 force-with-lease push.
# Best-effort (design v2 인정). 충돌/실패 시 abort + JSON ack로 manual 필요 보고.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

N=$(git log --since="yesterday 00:00" --until="today 00:00" --grep='^\[auto-sync\]' --oneline 2>/dev/null | wc -l | tr -d ' ')

if [ "${N:-0}" -lt 2 ]; then
    printf '{"squashed": false, "reason": "insufficient_commits", "count": %s, "pushed": false}\n' "${N:-0}"
    exit 0
fi

export GIT_SEQUENCE_EDITOR="$SCRIPT_DIR/squash_todo_edit.sh"

if ! REBASE_OUT=$(git rebase -i "HEAD~$N" 2>&1); then
    git rebase --abort 2>/dev/null || true
    REBASE_ERR_JSON=$(printf '%s' "$REBASE_OUT" | python3 -c "import sys, json; sys.stdout.write(json.dumps(sys.stdin.read()))")
    printf '{"squashed": false, "reason": "rebase_failed", "count": %s, "pushed": false, "error_msg": %s}\n' "$N" "$REBASE_ERR_JSON"
    exit 1
fi

if [ -z "$(git remote 2>/dev/null)" ]; then
    printf '{"squashed": true, "count": %s, "pushed": false, "reason": "no_remote"}\n' "$N"
    exit 0
fi

if PUSH_OUT=$(GIT_TERMINAL_PROMPT=0 git push --force-with-lease 2>&1); then
    printf '{"squashed": true, "count": %s, "pushed": true}\n' "$N"
else
    PUSH_ERR_JSON=$(printf '%s' "$PUSH_OUT" | python3 -c "import sys, json; sys.stdout.write(json.dumps(sys.stdin.read()))")
    printf '{"squashed": true, "count": %s, "pushed": false, "reason": "force_push_blocked", "error_msg": %s}\n' "$N" "$PUSH_ERR_JSON"
    exit 1
fi

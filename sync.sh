#!/bin/bash
# Hermes Multi-Agent Config — Sync Script
# ~/.hermes/ 안의 sync 가능 파일을 본 git repo로 내보냅니다.
# 새 머신 setup: git clone → bash restore.sh → .env/auth.json 별도 복원.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

echo "🔁 Hermes 설정을 $SCRIPT_DIR 으로 동기화..."

# 1. 프로필 (config.yaml + SOUL.md)
for profile in orchestrator sub-director researcher tech-artist dev-gemma; do
    PROFILE_DIR="$HERMES_HOME/profiles/$profile"
    DEST_DIR="$SCRIPT_DIR/profiles/$profile"
    mkdir -p "$DEST_DIR"
    [ -f "$PROFILE_DIR/config.yaml" ] && cp "$PROFILE_DIR/config.yaml" "$DEST_DIR/config.yaml" && echo "  ✓ profiles/$profile/config.yaml"
    [ -f "$PROFILE_DIR/SOUL.md" ]    && cp "$PROFILE_DIR/SOUL.md"    "$DEST_DIR/SOUL.md"    && echo "  ✓ profiles/$profile/SOUL.md"
done

# 2. 커스텀 skills (bundled 제외)
SKILLS_SRC="$HERMES_HOME/skills"
SKILLS_DEST="$SCRIPT_DIR/skills"
if [ -f "$SKILLS_SRC/.bundled_manifest" ]; then
    for skill_dir in "$SKILLS_SRC"/*/; do
        skill_name=$(basename "$skill_dir")
        if ! grep -q "\"$skill_name\"" "$SKILLS_SRC/.bundled_manifest" 2>/dev/null; then
            mkdir -p "$SKILLS_DEST/$skill_name"
            cp -r "$skill_dir"* "$SKILLS_DEST/$skill_name/" 2>/dev/null || true
            echo "  ✓ skills/$skill_name (custom)"
        fi
    done
else
    cp -r "$SKILLS_SRC/"* "$SKILLS_DEST/" 2>/dev/null || true
    echo "  ⚠ bundled_manifest 없음 — 전체 skills 복사됨"
fi

# 3. cron jobs.json
mkdir -p "$SCRIPT_DIR/cron"
[ -f "$HERMES_HOME/cron/jobs.json" ] && cp "$HERMES_HOME/cron/jobs.json" "$SCRIPT_DIR/cron/jobs.json" && echo "  ✓ cron/jobs.json"

# 4. 메인 config.yaml
[ -f "$HERMES_HOME/config.yaml" ] && cp "$HERMES_HOME/config.yaml" "$SCRIPT_DIR/config.yaml" && echo "  ✓ config.yaml"

# 5. patches/ (wiki_first_kb_second.py 등 — anthropic_billing_bypass는 install-remote.sh가 별도 관리)
mkdir -p "$SCRIPT_DIR/patches"
if [ -d "$HERMES_HOME/patches" ]; then
    for patch in "$HERMES_HOME/patches"/*.py; do
        [ -f "$patch" ] || continue
        # bypass 패치는 install-remote.sh가 자체 갱신 — sync 제외
        if [[ "$(basename "$patch")" == "anthropic_billing_bypass.py" ]]; then
            continue
        fi
        cp "$patch" "$SCRIPT_DIR/patches/" && echo "  ✓ patches/$(basename "$patch")"
    done
fi

# 6. bin/ (사용자 정의 도구만; quota.sh 등 Hermes 기본은 제외)
mkdir -p "$SCRIPT_DIR/bin"
if [ -d "$HERMES_HOME/bin" ]; then
    for tool in "$HERMES_HOME/bin"/*; do
        [ -f "$tool" ] || continue
        # Hermes 기본 도구 제외 목록 (필요 시 추가)
        case "$(basename "$tool")" in
            quota.sh) continue ;;  # Hermes 자체 제공
            tirith)   continue ;;  # Hermes 자체 binary (Mach-O, config.yaml의 tirith_path)
        esac
        cp "$tool" "$SCRIPT_DIR/bin/" && echo "  ✓ bin/$(basename "$tool")"
    done
fi

# 7. wiki/ (raw/ 와 graphify-out/ 제외 — 자동 생성/큰 파일)
WIKI_SRC="$HERMES_HOME/wiki"
WIKI_DEST="$SCRIPT_DIR/wiki"
if [ -d "$WIKI_SRC" ]; then
    mkdir -p "$WIKI_DEST"
    rsync -a \
      --delete \
      --exclude="raw/" \
      --exclude="graphify-out/" \
      --exclude="*.lock" \
      "$WIKI_SRC/" "$WIKI_DEST/" 2>/dev/null && echo "  ✓ wiki/ (raw, graphify-out 제외)"
fi

echo ""
echo "✅ 동기화 완료. git add + git commit + git push 진행하세요."
echo "   복원: bash $SCRIPT_DIR/restore.sh"

#!/bin/bash
# Hermes Multi-Agent Config - Sync Script
# Hermes 설정을 이 디렉토리로 내보냅니다.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

echo "🔁 Hermes 설정을 $SCRIPT_DIR 으로 동기화합니다..."

# 1. 프로필 설정 (config.yaml + SOUL.md)
for profile in orchestrator sub-director researcher tech-artist dev-gemma; do
    PROFILE_DIR="$HERMES_HOME/profiles/$profile"
    DEST_DIR="$SCRIPT_DIR/profiles/$profile"
    mkdir -p "$DEST_DIR"

    if [ -f "$PROFILE_DIR/config.yaml" ]; then
        cp "$PROFILE_DIR/config.yaml" "$DEST_DIR/config.yaml"
        echo "  ✓ profiles/$profile/config.yaml"
    fi

    if [ -f "$PROFILE_DIR/SOUL.md" ]; then
        cp "$PROFILE_DIR/SOUL.md" "$DEST_DIR/SOUL.md"
        echo "  ✓ profiles/$profile/SOUL.md"
    fi
done

# 2. 커스텀 스킬
SKILLS_SRC="$HERMES_HOME/skills"
SKILLS_DEST="$SCRIPT_DIR/skills"

# 번들 스킬 제외하고 사용자 정의 스킬만 복사
if [ -f "$SKILLS_SRC/.bundled_manifest" ]; then
    # bundled manifest에 없는 것만 복사
    for skill_dir in "$SKILLS_SRC"/*/; do
        skill_name=$(basename "$skill_dir")
        # .bundled_manifest에 있는지 확인
        if ! grep -q "\"$skill_name\"" "$SKILLS_SRC/.bundled_manifest" 2>/dev/null; then
            mkdir -p "$SKILLS_DEST/$skill_name"
            cp -r "$skill_dir"* "$SKILLS_DEST/$skill_name/" 2>/dev/null || true
            echo "  ✓ skills/$skill_name (custom)"
        fi
    done
else
    # bundled_manifest 없으면 전체 복사 (용량 주의)
    cp -r "$SKILLS_SRC/"* "$SKILLS_DEST/" 2>/dev/null || true
    echo "  ⚠ bundled_manifest 없음 - 전체 스킬 복사됨"
fi

# 3. 크론 작업
if [ -f "$HERMES_HOME/cron.db" ]; then
    cp "$HERMES_HOME/cron.db" "$SCRIPT_DIR/cron/cron.db" 2>/dev/null || true
    echo "  ✓ cron/cron.db"
fi

# 4. 메인 config (참고용)
if [ -f "$HERMES_HOME/config.yaml" ]; then
    cp "$HERMES_HOME/config.yaml" "$SCRIPT_DIR/config.yaml"
    echo "  ✓ config.yaml (root)"
fi

echo ""
echo "✅ 동기화 완료!"
echo "   이제 git add + git commit + git push 하세요."
echo ""
echo "   복원은: bash $SCRIPT_DIR/restore.sh"

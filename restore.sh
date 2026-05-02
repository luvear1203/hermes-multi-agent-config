#!/bin/bash
# Hermes Multi-Agent Config - Restore Script
# GitHub에서 클론한 설정을 Hermes로 복원합니다.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

echo "🔄 Hermes 설정을 $SCRIPT_DIR 에서 복원합니다..."
echo ""

# 사전 체크
if ! command -v hermes &> /dev/null; then
    echo "❌ hermes 명령어를 찾을 수 없습니다. 먼저 Hermes Agent를 설치하세요."
    echo "   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash"
    exit 1
fi

# 1. 프로필 복원
for profile_dir in "$SCRIPT_DIR"/profiles/*/; do
    profile=$(basename "$profile_dir")
    PROFILE_DEST="$HERMES_HOME/profiles/$profile"

    # 프로필이 없으면 생성
    if [ ! -d "$PROFILE_DEST" ]; then
        echo "  📝 프로필 생성: $profile"
        hermes profile create "$profile" 2>/dev/null || {
            echo "  ⚠ hermes profile create 실패, 수동으로 생성합니다..."
            mkdir -p "$PROFILE_DEST"
        }
    fi

    # config.yaml 복원
    if [ -f "$profile_dir/config.yaml" ]; then
        cp "$profile_dir/config.yaml" "$PROFILE_DEST/config.yaml"
        echo "  ✓ $profile/config.yaml 복원"
    fi

    # SOUL.md 복원
    if [ -f "$profile_dir/SOUL.md" ]; then
        cp "$profile_dir/SOUL.md" "$PROFILE_DEST/SOUL.md"
        echo "  ✓ $profile/SOUL.md 복원"
    fi
done

# 2. 커스텀 스킬 복원
if [ -d "$SCRIPT_DIR/skills" ] && [ "$(ls -A "$SCRIPT_DIR/skills" 2>/dev/null)" ]; then
    echo ""
    echo "  📚 커스텀 스킬 복원 중..."
    for skill_dir in "$SCRIPT_DIR"/skills/*/; do
        skill_name=$(basename "$skill_dir")
        SKILL_DEST="$HERMES_HOME/skills/$skill_name"
        mkdir -p "$SKILL_DEST"
        cp -r "$skill_dir"* "$SKILL_DEST/" 2>/dev/null || true
        echo "  ✓ skills/$skill_name"
    done
fi

# 3. 크론 작업 복원
if [ -f "$SCRIPT_DIR/cron/cron.db" ]; then
    cp "$SCRIPT_DIR/cron/cron.db" "$HERMES_HOME/cron.db" 2>/dev/null || true
    echo "  ✓ cron.db 복원"
fi

# 4. 메인 config (참고용 - 덮어쓰지 않음)
if [ -f "$SCRIPT_DIR/config.yaml" ] && [ ! -f "$HERMES_HOME/config.yaml" ]; then
    cp "$SCRIPT_DIR/config.yaml" "$HERMES_HOME/config.yaml"
    echo "  ✓ config.yaml 복원"
fi

echo ""
echo "✅ 복원 완료!"
echo ""
echo "⚠️  .env 파일은 보안상 복원되지 않습니다. 직접 API 키를 설정하세요:"
echo "   orchestrator setup    # DeepSeek API 키"
echo "   researcher setup       # Anthropic API 키"
echo "   dev-gemma setup        # Gemma 4 (Ollama) 설정"
echo ""
echo "📋 프로필 목록:"
hermes profile list 2>/dev/null || echo "  (hermes 명령어 확인 필요)"

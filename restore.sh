#!/bin/bash
# Hermes Multi-Agent Config — Restore Script
# 새 머신: git clone → bash restore.sh.
# .env / auth.json 은 보안상 git 미포함 — 별도 절차 (README.md §"새 머신 setup" 참조).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

echo "🔄 Hermes 설정을 $SCRIPT_DIR 에서 $HERMES_HOME 으로 복원..."
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
    if [ ! -d "$PROFILE_DEST" ]; then
        echo "  📝 프로필 생성: $profile"
        hermes profile create "$profile" 2>/dev/null || mkdir -p "$PROFILE_DEST"
    fi
    [ -f "$profile_dir/config.yaml" ] && cp "$profile_dir/config.yaml" "$PROFILE_DEST/config.yaml" && echo "  ✓ $profile/config.yaml"
    [ -f "$profile_dir/SOUL.md" ]    && cp "$profile_dir/SOUL.md"    "$PROFILE_DEST/SOUL.md"    && echo "  ✓ $profile/SOUL.md"
done

# 2. 커스텀 skills 복원
if [ -d "$SCRIPT_DIR/skills" ] && [ "$(ls -A "$SCRIPT_DIR/skills" 2>/dev/null)" ]; then
    echo ""
    echo "  📚 skills 복원..."
    for skill_dir in "$SCRIPT_DIR"/skills/*/; do
        skill_name=$(basename "$skill_dir")
        SKILL_DEST="$HERMES_HOME/skills/$skill_name"
        mkdir -p "$SKILL_DEST"
        cp -r "$skill_dir"* "$SKILL_DEST/" 2>/dev/null || true
        echo "  ✓ skills/$skill_name"
    done
fi

# 3. cron jobs.json 복원 + orchestrator profile symlink (gateway dual-use 패턴)
if [ -f "$SCRIPT_DIR/cron/jobs.json" ]; then
    mkdir -p "$HERMES_HOME/cron"
    cp "$SCRIPT_DIR/cron/jobs.json" "$HERMES_HOME/cron/jobs.json"
    echo "  ✓ cron/jobs.json"
    # orchestrator profile에 global jobs.json symlink (Discord + cron 공존 패턴, memory feedback_hermes_gateway_dual_use)
    mkdir -p "$HERMES_HOME/profiles/orchestrator/cron"
    ln -sf "$HERMES_HOME/cron/jobs.json" "$HERMES_HOME/profiles/orchestrator/cron/jobs.json"
    echo "  ✓ profiles/orchestrator/cron/jobs.json -> $HERMES_HOME/cron/jobs.json (symlink)"
fi

# 4. 메인 config (이미 있으면 보존, 없으면 복사)
if [ -f "$SCRIPT_DIR/config.yaml" ]; then
    if [ -f "$HERMES_HOME/config.yaml" ]; then
        cp "$HERMES_HOME/config.yaml" "$HERMES_HOME/config.yaml.pre-restore"
        echo "  ⓘ 기존 config.yaml 백업: ~/.hermes/config.yaml.pre-restore"
    fi
    cp "$SCRIPT_DIR/config.yaml" "$HERMES_HOME/config.yaml"
    echo "  ✓ config.yaml"
fi

# 5. patches/ 복원
if [ -d "$SCRIPT_DIR/patches" ] && [ "$(ls -A "$SCRIPT_DIR/patches" 2>/dev/null)" ]; then
    mkdir -p "$HERMES_HOME/patches"
    cp "$SCRIPT_DIR/patches"/*.py "$HERMES_HOME/patches/" 2>/dev/null && echo "  ✓ patches/*.py"
fi

# 6. bin/ 복원 (실행 권한 부여)
if [ -d "$SCRIPT_DIR/bin" ] && [ "$(ls -A "$SCRIPT_DIR/bin" 2>/dev/null)" ]; then
    mkdir -p "$HERMES_HOME/bin"
    cp "$SCRIPT_DIR/bin"/* "$HERMES_HOME/bin/" 2>/dev/null
    chmod +x "$HERMES_HOME/bin"/* 2>/dev/null
    echo "  ✓ bin/*"
fi

# 7. wiki 복원 (raw/ 와 graphify-out/ 은 새 머신에서 비어있게 시작)
if [ -d "$SCRIPT_DIR/wiki" ] && [ "$(ls -A "$SCRIPT_DIR/wiki" 2>/dev/null)" ]; then
    mkdir -p "$HERMES_HOME/wiki"
    rsync -a "$SCRIPT_DIR/wiki/" "$HERMES_HOME/wiki/" 2>/dev/null && echo "  ✓ wiki/ (raw, graphify-out 미포함 — 필요 시 별도 복원)"
fi

echo ""
echo "✅ 파일 복원 완료."
echo ""
echo "📋 다음 수동 단계 (보안·OAuth 자료):"
echo "  1. ~/.hermes/.env  — API keys (QDRANT_URL/_API_KEY, VOYAGE_API_KEY, TAVILY_API_KEY,"
echo "                       GOOGLE_API_KEY x2, DEEPSEEK_API_KEY, DISCORD_BOT_TOKEN,"
echo "                       DISCORD_ALERT_USER_ID 등). 별도 안전 backup에서 복원."
echo "  2. Anthropic Max OAuth 로그인:    claude setup-token 또는 claude login"
echo "  3. OpenAI Codex OAuth 로그인:     codex login"
echo "  4. Bypass 5종 패치 재설치:"
echo "       curl -fsSL https://raw.githubusercontent.com/kristianvast/hermes-claude-auth/main/install-remote.sh | bash"
echo "  5. Gateway 등록 (orchestrator profile 단독, Discord+cron 공존):"
echo "       hermes --profile orchestrator gateway install"
echo "       launchctl unload ~/Library/LaunchAgents/ai.hermes.gateway.plist  # default profile 비활성"
echo "  6. macOS sleep 정책 (M1 Air lid-close 운용):"
echo "       sudo pmset -a tcpkeepalive 1"
echo "       sudo pmset -a powernap 1"
echo "       sudo pmset repeat wakeorpoweron MTWRFSU 02:55:00"
echo "  7. 검증: hermes status / hermes cron status / 7-profile smoke test"
echo ""
echo "📋 프로필 목록:" && hermes profile list 2>/dev/null || echo "  (hermes 명령어 확인 필요)"

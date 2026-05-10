"""External-service quota alert helper.

Sends Discord DM to user when Voyage / Qdrant / Tavily / arXiv hits a hard
quota / rate-limit / persistent error. Director/Sub-Director excluded
(those are Anthropic Max OAuth + Codex OAuth subscription paths — not API quota).

Env required (~/.hermes/.env):
  DISCORD_BOT_TOKEN — Hermes bot token (already set)
  DISCORD_ALERT_USER_ID — your Discord user numeric ID (set this per Plan PC-1)
"""
from __future__ import annotations
import os
import json
import time
import requests
from datetime import datetime, timezone
from pathlib import Path


def _read_env(key: str) -> str | None:
    """Same helper as kb_tools._read_env. Returns None if missing."""
    env_path = os.path.expanduser("~/.hermes/.env")
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    if k.strip() == key:
                        return v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return None


def _env(key: str) -> str | None:
    return os.environ.get(key) or _read_env(key)


_LAST_ALERT_PATH = Path.home() / ".hermes" / "cron" / "output" / "last_quota_alert.json"
_DEDUPE_WINDOW_SEC = 3600  # don't re-alert same (service, error_class) within 1 hour


def _should_alert(service: str, error_class: str) -> bool:
    """Dedupe: skip alert if same (service,error_class) fired within last hour."""
    try:
        data = json.loads(_LAST_ALERT_PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    key = f"{service}:{error_class}"
    last_ts = data.get(key, 0)
    now = time.time()
    if now - last_ts < _DEDUPE_WINDOW_SEC:
        return False
    data[key] = now
    _LAST_ALERT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LAST_ALERT_PATH.write_text(json.dumps(data, indent=2))
    return True


def alert_quota(service: str, error_class: str, error_msg: str, *,
                upgrade_hint: str = "", force: bool = False) -> bool:
    """Send Discord DM to user about quota/rate-limit hit.

    Args:
      service: "voyage" | "qdrant" | "tavily" | "arxiv" | "semantic_scholar" | "github"
      error_class: "rate_limit" | "quota_exhausted" | "storage_full" | "persistent_5xx"
      error_msg: short error message (truncated to 500 chars)
      upgrade_hint: optional one-line action recommendation
      force: skip dedupe (use sparingly)

    Returns True if sent, False if deduped or missing config.
    """
    if not force and not _should_alert(service, error_class):
        return False

    bot_token = _env("DISCORD_BOT_TOKEN")
    user_id = _env("DISCORD_ALERT_USER_ID")
    if not bot_token or not user_id:
        print(f"[quota_alert] missing DISCORD_BOT_TOKEN or DISCORD_ALERT_USER_ID; "
              f"would have alerted: {service}/{error_class}", flush=True)
        return False

    # 1. Open DM channel with user
    r = requests.post(
        "https://discord.com/api/v10/users/@me/channels",
        headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
        json={"recipient_id": user_id}, timeout=15,
    )
    r.raise_for_status()
    channel_id = r.json()["id"]

    # 2. Compose message
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    msg = (
        f"⚠️ **Hermes 외부 API quota 알림** ({ts})\n"
        f"```\n"
        f"Service:     {service}\n"
        f"Error class: {error_class}\n"
        f"Message:     {error_msg[:500]}\n"
        f"```\n"
    )
    if upgrade_hint:
        msg += f"**조치 권장**: {upgrade_hint}\n"
    msg += f"\n_dedupe: {_DEDUPE_WINDOW_SEC // 60}분 내 동일 알림 억제. force=true로 우회_"

    # 3. Post message
    r = requests.post(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        headers={"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"},
        json={"content": msg}, timeout=15,
    )
    r.raise_for_status()
    return True


# Per-service hint table
UPGRADE_HINTS = {
    ("voyage", "rate_limit"):       "Voyage Free TPM 한도 도달. 6시간 cycle 분산 또는 Voyage 유료 plan 검토.",
    ("voyage", "quota_exhausted"):  "Voyage 월 50M tokens 한도 임박. https://dash.voyageai.com → Plan 업그레이드.",
    ("qdrant", "storage_full"):     "Qdrant Cloud free tier (1GB RAM / 4GB storage) 초과. https://cloud.qdrant.io → paid ($25/월) 검토.",
    ("qdrant", "rate_limit"):       "Qdrant rate limit. paid tier로 더 높은 RPS 가능.",
    ("tavily", "quota_exhausted"):  "Tavily 월 query 한도 초과. https://app.tavily.com → 유료 plan 검토.",
    ("tavily", "rate_limit"):       "Tavily rate limit. 유료 plan 또는 weekly cron만 사용.",
    ("arxiv", "persistent_5xx"):    "arxiv free anonymous IP throttle 지속. 다음 cycle에서 자연 회복 또는 source 임시 비활성 검토.",
    ("semantic_scholar", "persistent_5xx"): "Semantic Scholar IP throttle 지속. 다음 cycle 자연 회복 또는 API key 발급(https://www.semanticscholar.org/product/api).",
    ("github", "rate_limit"):       "GitHub 60req/hr (무토큰) 초과. https://github.com/settings/tokens → public_repo scope token 발급 후 .env GITHUB_TOKEN 설정.",
}


def alert_with_hint(service: str, error_class: str, error_msg: str, *, force: bool = False) -> bool:
    """Convenience: lookup upgrade_hint from UPGRADE_HINTS table."""
    hint = UPGRADE_HINTS.get((service, error_class), "외부 서비스 상태 점검 권장.")
    return alert_quota(service, error_class, error_msg, upgrade_hint=hint, force=force)


if __name__ == "__main__":
    # Smoke test
    import sys
    args = sys.argv[1:]
    if not args:
        print("usage: python quota_alert.py <service> <error_class> <message> [--force]")
        print("       services: voyage|qdrant|tavily|arxiv|semantic_scholar|github")
        sys.exit(1)
    service, error_class = args[0], args[1]
    msg = args[2] if len(args) > 2 else "test alert"
    force = "--force" in args
    sent = alert_with_hint(service, error_class, msg, force=force)
    print(f"sent: {sent}")

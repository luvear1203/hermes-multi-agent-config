"""Generate Telegram-formatted topic approval card. User responds with
'approve <name>' / 'reject <name>' / 'rename <name> <newname>' messages.

Run by cron job topic_curation_weekly.
"""
from __future__ import annotations
from pathlib import Path
import topic_recommender


def main() -> int:
    candidates = topic_recommender.recommend(top_n=12)
    out_path = Path.home() / ".hermes" / "cron" / "output" / "topic_curation_card.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Topic Curation Card", "", "추천 토픽. Telegram에 답장으로 결정 (approve/reject/rename):", ""]
    for c in candidates:
        kw = ", ".join(c["keywords"])
        lines.append(f"- **{c['name']}** (score={c['score']}, src={c['source']}, keywords=[{kw}])")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

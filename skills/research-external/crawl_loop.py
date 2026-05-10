"""Continuous Researcher cron loop.

Invoked by cron prompts (Plan Step 3 Task 20):
  python ~/.hermes/skills/research-external/crawl_loop.py --mode daily
  python ~/.hermes/skills/research-external/crawl_loop.py --mode weekly

For each active topic in `topics` collection, query external sources, normalize,
dedupe-upsert into KB. Append a one-line summary to ~/.hermes/wiki/log.md.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "knowledge-db"))
sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "research-external"))

from kb_tools import kb_topic_list, kb_upsert  # noqa: E402
from external_tools import (  # noqa: E402
    arxiv_search, github_search, semantic_scholar_search, tavily_search,
)


DAILY_SOURCES = (
    ("arxiv", arxiv_search, {"since_days": 1, "max_results": 5}),
    ("github", github_search, {"since_days": 1, "limit": 5}),
)

WEEKLY_SOURCES = (
    ("arxiv", arxiv_search, {"since_days": 7, "max_results": 5}),
    ("semantic_scholar", semantic_scholar_search, {"limit": 5}),
    ("github", github_search, {"since_days": 7, "limit": 5}),
    ("tavily", tavily_search, {"max_results": 5}),
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
            chunks = fn(query, **kwargs)
        except Exception as e:
            counts["errors"] += 1
            print(f"  [{src_name}] error: {e}", file=sys.stderr)
            continue
        for c in chunks:
            text = c.pop("_text", "") or c.get("title", "")
            if not text:
                continue  # Voyage rejects empty input
            payload = {**c, "relevance_topics": [topic["name"]]}
            # confidence is pre-set by normalize_chunk; ensure required fields exist
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

    log = Path.home() / ".hermes" / "wiki" / "log.md"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    line = f"\n## [{today}] crawl | mode={args.mode} | "
    line += " · ".join(f"{n}: +{c['created']}/dup{c['skipped_dedupe']}" for n, c in per_topic)
    line += f" | total +{total['created']} new (errors={total['errors']})"
    with log.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)
    return 0 if total["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

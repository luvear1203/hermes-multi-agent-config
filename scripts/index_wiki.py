"""Index the entire ~/.hermes/wiki into 3 KB collections (wiki_entities,
wiki_concepts, wiki_architecture) on first pass.

Idempotent via dedupe (content_hash + point_id). Re-runnable.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "knowledge-db"))
from kb_tools import kb_upsert_batch  # noqa: E402

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


def build_item(path: Path) -> dict | None:
    """Return {collection, text, payload, point_id} for a wiki page, or None to skip."""
    rel = path.relative_to(WIKI)
    coll = route_collection(rel)
    if not coll:
        return None
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
    return {"collection": coll, "text": text, "payload": payload, "point_id": path.stem}


CHUNK_SIZE = 5      # Voyage Free TPM ~10K/min; ~5 pages/chunk fits typical wiki page
SLEEP_BETWEEN = 25  # seconds between chunks (Voyage Free ~3 RPM safety margin)


def main() -> int:
    import time as _time
    by_coll: dict[str, list[dict]] = {}
    skipped_route = 0
    for page in WIKI.rglob("*.md"):
        if "raw/" in str(page) or page.name in ("CLAUDE.md", "SCHEMA.md", "log.md", "index.md"):
            continue
        if "graphify-out/" in str(page):
            continue
        item = build_item(page)
        if item is None:
            skipped_route += 1
            continue
        by_coll.setdefault(item["collection"], []).append(item)

    totals = {"created": 0, "skipped_dedupe": 0, "skipped_route": skipped_route}
    chunk_index = 0
    for coll, items in by_coll.items():
        print(f"=== {coll}: {len(items)} pages, chunked CHUNK_SIZE={CHUNK_SIZE} ===")
        for i in range(0, len(items), CHUNK_SIZE):
            chunk = items[i:i + CHUNK_SIZE]
            if chunk_index > 0:
                print(f"  ... sleep {SLEEP_BETWEEN}s (Voyage Free TPM safety)")
                _time.sleep(SLEEP_BETWEEN)
            result = kb_upsert_batch(coll, chunk)
            for k, v in result.items():
                totals[k] = totals.get(k, 0) + v
            print(f"  chunk {i//CHUNK_SIZE + 1}/{(len(items)+CHUNK_SIZE-1)//CHUNK_SIZE}: {result}")
            chunk_index += 1
    print(f"\nTotals: {totals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Index mythrill-pipeline/src/ into mythrill_code collection.

One chunk per .py file. Uses kb_upsert_batch + chunked sleep for Voyage Free TPM.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "knowledge-db"))
from kb_tools import kb_upsert_batch  # noqa: E402

ROOT = Path.home() / "mythrill-pipeline" / "src"
CHUNK_SIZE = 5
SLEEP_BETWEEN = 25


def build_item(py: Path) -> dict:
    text = py.read_text(encoding="utf-8")
    rel = py.relative_to(ROOT.parent)
    return {
        "collection": "mythrill_code",
        "text": text,
        "payload": {
            "source_url": f"file://{py}",
            "citation": f"mythrill:{rel}",
            "file_path": str(rel),
            "language": "en",
            "confidence": "high",
            "embedding_model": "voyage-3",
            "module": str(rel.parent),
        },
        "point_id": str(rel).replace("/", "_").replace(".", "_"),
    }


def main() -> int:
    items: list[dict] = []
    skipped_empty = 0
    for py in ROOT.rglob("*.py"):
        if "__pycache__" in str(py) or "venv" in str(py):
            continue
        if py.stat().st_size == 0:
            skipped_empty += 1
            continue
        items.append(build_item(py))
    print(f"  (skipped {skipped_empty} empty .py files)")

    print(f"=== mythrill_code: {len(items)} files, chunked CHUNK_SIZE={CHUNK_SIZE} ===")
    totals = {"created": 0, "skipped_dedupe": 0}
    for i in range(0, len(items), CHUNK_SIZE):
        if i > 0:
            print(f"  ... sleep {SLEEP_BETWEEN}s (Voyage Free TPM safety)")
            time.sleep(SLEEP_BETWEEN)
        chunk = items[i:i + CHUNK_SIZE]
        result = kb_upsert_batch("mythrill_code", chunk)
        for k, v in result.items():
            totals[k] = totals.get(k, 0) + v
        print(f"  chunk {i // CHUNK_SIZE + 1}/{(len(items) + CHUNK_SIZE - 1) // CHUNK_SIZE}: {result}")
    print(f"\nTotals: {totals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

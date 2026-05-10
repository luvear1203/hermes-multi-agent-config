"""Topic Tracker — extract candidate topics from mythrill modules and wiki tags."""
from __future__ import annotations
from collections import Counter
from pathlib import Path

import yaml

WIKI = Path.home() / ".hermes" / "wiki"
MYTHRILL_SRC = Path.home() / "mythrill-pipeline" / "src"


def from_wiki_tags() -> Counter:
    c: Counter = Counter()
    for sub in ("concepts", "entities"):
        for page in (WIKI / sub).glob("*.md"):
            text = page.read_text(encoding="utf-8")
            if not text.startswith("---"):
                continue
            try:
                fm = yaml.safe_load(text.split("---", 2)[1]) or {}
                for tag in fm.get("tags", []) or []:
                    c[tag] += 1
            except Exception:
                pass
    return c


def from_mythrill_modules() -> Counter:
    c: Counter = Counter()
    if not MYTHRILL_SRC.exists():
        return c
    for d in MYTHRILL_SRC.iterdir():
        if d.is_dir() and not d.name.startswith("__"):
            c[f"mythrill_{d.name}"] += 1
    return c


def recommend(top_n: int = 12) -> list[dict]:
    tags = from_wiki_tags()
    modules = from_mythrill_modules()
    merged = tags + modules
    out = []
    for name, count in merged.most_common(top_n):
        out.append({
            "name": name,
            "score": count,
            "keywords": [name.replace("_", " ").replace("-", " ")],
            "source": "wiki_tags" if name in tags else "mythrill_module",
        })
    return out


def main() -> int:
    import json
    candidates = recommend()
    print(json.dumps(candidates, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

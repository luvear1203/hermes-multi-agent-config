"""Wiki page compression — convert verbose pages to dense form (header table +
summary paragraph + raw archive link). User-approved targets only (audit-final).
"""
from __future__ import annotations
import json
import re
import shutil
from pathlib import Path

import yaml

WIKI = Path.home() / ".hermes" / "wiki"
RAW_ARCHIVE = WIKI / "raw" / "compressed_2026-05-10"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}, text
    fm = yaml.safe_load(text[3:end]) or {}
    body = text[end + 3:].lstrip()
    return fm, body


def first_paragraph(body: str) -> str:
    parts = re.split(r"\n\s*\n", body.strip(), maxsplit=2)
    return parts[0] if parts else ""


def compress_page(path: Path, content: str | None = None) -> str:
    text = content if content is not None else path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    fm["updated"] = "2026-05-10"
    fm.setdefault("compressed", True)
    summary = first_paragraph(body)[:1500]
    archive_rel = f"raw/compressed_2026-05-10/{path.name}"
    new_body = (
        f"# {fm.get('title', path.stem)}\n\n"
        f"> Compressed 2026-05-10. Original at [[{archive_rel}]].\n\n"
        f"## Summary\n\n{summary}\n\n"
        f"## 원본 보존\n\n[원본 보존: {archive_rel}](../{archive_rel})\n"
    )
    fm_str = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{fm_str}\n---\n\n{new_body}"


def main() -> int:
    final = json.loads((Path.home() / "hermes-multi-agent-config" / "docs" / "superpowers" / "audit-2026-05-10-final.json").read_text())
    targets = final["compress_targets"]
    RAW_ARCHIVE.mkdir(parents=True, exist_ok=True)
    n = 0
    for rel in targets:
        path = WIKI / rel
        if not path.exists():
            print(f"  missing: {rel}")
            continue
        shutil.copy2(path, RAW_ARCHIVE / path.name)
        path.write_text(compress_page(path), encoding="utf-8")
        n += 1
        print(f"  compressed: {rel}")
    print(f"\nCompressed {n} pages → {RAW_ARCHIVE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

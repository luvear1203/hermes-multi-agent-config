"""Wiki audit — classify each page as preserve / compress / review.

Used by Step 0 of the 2026-05-10 Hermes rebuild plan. Output is a JSON report
the user reviews and confirms before Step 4 compression.

Usage:
    python audit_wiki.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Literal

Category = Literal["preserve", "compress", "review"]

# Patterns from spec §3.1 of 2026-05-10-hermes-rebuild-and-knowledge-db-design.md
COMPRESS_PATTERNS = (
    "handoff/",
    "llm1-validation",
    "mythrill-spike-",
)

PRESERVE_PATTERNS = (
    "architecture/",
    "c-chasm-ip-core",
    "c-chasm-five-laws",
    "mythrill-architecture",
    "llm-separation-design",
    "mpm-constitutive-equation-swap",
    "three-deity-types",
    "dual-ending-branch",
    "강림형_신",
    "회귀형_신",
    "광기형_신",
    "신의_세_유형",
    "매크로_팩션_구조",
    "cosmic-horror",
    "stage-separation-rule",
    "trigger-classification",
    "naked-viewer",
    "natural-language-vfx-pipeline",
    "visual-inference-policy",
    "vfx-input-labeling-guide",
    "pre-bake-vfx-workflow",
    "정렬",
    "아자토스의_꿈_패턴",
    "C-Chasm_우주론",
    "본편_RPG",
    "아담",
    "연금술_7단계_시스템",
    "grand-engine-vision",
    "mythrill-pipeline",
    "mythrill-roadmap",
    "mythrill-architecture",
)


def classify_page(page: Path, content: str) -> Category:
    rel = str(page).replace("\\", "/")
    for pat in COMPRESS_PATTERNS:
        if pat in rel:
            return "compress"
    for pat in PRESERVE_PATTERNS:
        if pat in rel:
            return "preserve"
    return "review"


def audit_wiki(wiki_root: Path) -> dict[Category, list[dict]]:
    report: dict[Category, list[dict]] = {"preserve": [], "compress": [], "review": []}
    for page in wiki_root.rglob("*.md"):
        rel_str = str(page.relative_to(wiki_root))
        if rel_str.startswith("raw/") or rel_str.startswith("graphify-out/"):
            continue
        try:
            content = page.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        cat = classify_page(page.relative_to(wiki_root), content)
        size = page.stat().st_size
        wikilinks = content.count("[[")
        report[cat].append({
            "path": rel_str,
            "size_bytes": size,
            "wikilinks": wikilinks,
        })
    return report


def main() -> int:
    wiki_root = Path.home() / ".hermes" / "wiki"
    if not wiki_root.exists():
        print(f"wiki not found: {wiki_root}", file=sys.stderr)
        return 1
    report = audit_wiki(wiki_root)
    out_path = Path(__file__).parent.parent / "docs" / "superpowers" / "audit-2026-05-10.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"audit report: {out_path}")
    print(f"  preserve : {len(report['preserve'])} pages")
    print(f"  compress : {len(report['compress'])} pages")
    print(f"  review   : {len(report['review'])} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

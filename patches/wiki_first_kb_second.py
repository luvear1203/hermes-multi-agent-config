"""Wiki-First → KB-Second search hook.

Hooks into orchestrator's Wiki-First search routine. When the in-memory wiki
graph traversal returns < THRESHOLD relevance, fall through to KB search across
wiki_* collections, then kb_* collections.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "knowledge-db"))
from kb_tools import kb_search  # noqa: E402

THRESHOLD = 0.5
WIKI_COLLECTIONS = ("wiki_architecture", "wiki_entities", "wiki_concepts")
KB_COLLECTIONS = ("kb_papers", "kb_oss_projects", "kb_dev_docs", "kb_industry_solutions", "kb_lessons_learned")


def search(query: str, top_k: int = 8) -> list[dict]:
    """Two-tier search. Returns chunks with source_url + citation."""
    hits: list[dict] = []
    for coll in WIKI_COLLECTIONS:
        try:
            res = kb_search(coll, query, top_k=top_k // 2)
        except Exception:
            continue
        for r in res:
            score = r.get("score", 0.0)
            if score >= THRESHOLD:
                hits.append({"collection": coll, "score": score, "payload": r["payload"]})
    if hits:
        return sorted(hits, key=lambda h: h["score"], reverse=True)[:top_k]

    for coll in KB_COLLECTIONS:
        try:
            res = kb_search(coll, query, top_k=top_k // 2)
        except Exception:
            continue
        for r in res:
            hits.append({"collection": coll, "score": r.get("score", 0.0), "payload": r["payload"]})
    return sorted(hits, key=lambda h: h["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    import json
    q = " ".join(sys.argv[1:]) or "mpm constitutive equation"
    print(json.dumps(search(q), indent=2, ensure_ascii=False)[:2000])

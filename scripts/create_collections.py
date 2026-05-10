"""Create the 12 Qdrant collections for the Hermes Knowledge DB.

Run once during Step 2. Idempotent — skips existing collections.
"""
from __future__ import annotations
import os
import requests
from typing import Any

DIM = 1024  # voyage-3 / bge-m3 both produce 1024-dim vectors

COLLECTIONS: list[dict[str, Any]] = [
    {"name": "wiki_entities",        "kind": "vector"},
    {"name": "wiki_concepts",        "kind": "vector"},
    {"name": "wiki_architecture",    "kind": "vector"},
    {"name": "kb_papers",            "kind": "vector"},
    {"name": "kb_oss_projects",      "kind": "vector"},
    {"name": "kb_industry_solutions","kind": "vector"},
    {"name": "kb_lessons_learned",   "kind": "vector"},
    {"name": "kb_dev_docs",          "kind": "vector"},
    {"name": "mythrill_code",        "kind": "vector"},
    {"name": "chat_memory",          "kind": "vector"},
    {"name": "personal_notes",       "kind": "vector"},
    {"name": "topics",               "kind": "metadata"},
]


def build_create_request(name: str) -> dict[str, Any]:
    spec = next(c for c in COLLECTIONS if c["name"] == name)
    if spec["kind"] == "metadata":
        # Qdrant rejects vectors.size=0. Use 1-dim placeholder; queries use payload filter.
        return {"vectors": {"size": 1, "distance": "Cosine"}}
    return {
        "vectors": {"size": DIM, "distance": "Cosine"},
        "hnsw_config": {"m": 16, "ef_construct": 100},
        "quantization_config": {"scalar": {"type": "int8", "always_ram": True}},
    }


def _read_env(key: str) -> str:
    """Hermes .env tolerates spaces around `=`; shell source does not. Read directly."""
    env_path = os.path.expanduser("~/.hermes/.env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    raise KeyError(f"{key} not found in {env_path}")


def create(url: str, api_key: str, name: str) -> str:
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    r = requests.get(f"{url}/collections/{name}", headers=headers, timeout=30)
    if r.status_code == 200:
        return "exists"
    body = build_create_request(name)
    r = requests.put(f"{url}/collections/{name}", headers=headers, json=body, timeout=30)
    r.raise_for_status()
    return "created"


def main() -> int:
    url = (os.environ.get("QDRANT_URL") or _read_env("QDRANT_URL")).rstrip("/")
    api_key = os.environ.get("QDRANT_API_KEY") or _read_env("QDRANT_API_KEY")
    for spec in COLLECTIONS:
        status = create(url, api_key, spec["name"])
        print(f"{spec['name']:30s} {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

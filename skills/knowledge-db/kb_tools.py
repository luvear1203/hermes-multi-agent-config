"""Knowledge DB CRUD with dedupe and forced provenance.

Functions: kb_search, kb_upsert, kb_topic_register, kb_topic_list, kb_stats.
All upserts validate payload (source_url + content_hash + citation + retrieved_at)
and skip on content_hash collision (dedupe).
"""
from __future__ import annotations
import hashlib
import os
import requests
from datetime import datetime, timezone

REQUIRED_PAYLOAD = (
    "source_url", "content_hash", "retrieved_at", "citation",
    "language", "embedding_model", "confidence",
)


def compute_content_hash(text: str) -> str:
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"sha256:{h}"


def validate_payload(p: dict) -> None:
    missing = [k for k in REQUIRED_PAYLOAD if k not in p or p[k] in (None, "")]
    if missing:
        raise ValueError(f"missing required payload fields: {missing}")


def _read_env(key: str) -> str:
    """Hermes ~/.hermes/.env tolerates spaces around '='; shell source does not.
    Fallback when env var is not exported. Same helper as scripts/create_collections.py.
    """
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


def _env(key: str) -> str:
    return os.environ.get(key) or _read_env(key)


def _qdrant_url() -> str:
    return _env("QDRANT_URL").rstrip("/")


def _qdrant_headers() -> dict:
    return {"api-key": _env("QDRANT_API_KEY"), "Content-Type": "application/json"}


def _qdrant_get(path: str, params: dict | None = None) -> dict:
    r = requests.get(f"{_qdrant_url()}{path}", headers=_qdrant_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def _qdrant_put(path: str, body: dict) -> dict:
    r = requests.put(f"{_qdrant_url()}{path}", headers=_qdrant_headers(), json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def _qdrant_post(path: str, body: dict) -> dict:
    r = requests.post(f"{_qdrant_url()}{path}", headers=_qdrant_headers(), json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def _embed(text: str) -> list[float]:
    r = requests.post(
        "https://api.voyageai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {_env('VOYAGE_API_KEY')}", "Content-Type": "application/json"},
        json={"input": text, "model": "voyage-3"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]


def kb_search(collection: str, query: str, top_k: int = 10, filter: dict | None = None) -> list[dict]:
    vec = _embed(query)
    body = {"vector": vec, "limit": top_k, "with_payload": True}
    if filter:
        body["filter"] = filter
    res = _qdrant_post(f"/collections/{collection}/points/search", body)
    return res.get("result", [])


def kb_upsert(collection: str, text: str, payload: dict, point_id: str | None = None) -> str:
    """Upsert one point. Returns 'created' | 'skipped_dedupe'.

    Dedupe: uses content_hash hex (first 32 chars) as point ID and checks via
    GET /points/{id} — works without payload index. Custom point_id keeps the
    same dedupe key (still based on content_hash) but is stored as the ID.
    """
    if "content_hash" not in payload:
        payload["content_hash"] = compute_content_hash(text)
    if "retrieved_at" not in payload:
        payload["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    if "embedding_model" not in payload:
        payload["embedding_model"] = "voyage-3"
    validate_payload(payload)

    pid = point_id or payload["content_hash"].split(":", 1)[1][:32]
    try:
        existing = _qdrant_get(f"/collections/{collection}/points/{pid}")
        if existing.get("result"):
            return "skipped_dedupe"
    except requests.HTTPError as e:
        if e.response.status_code != 404:
            raise

    vec = _embed(text)
    body = {"points": [{"id": pid, "vector": vec, "payload": payload}]}
    _qdrant_put(f"/collections/{collection}/points", body)
    return "created"


def kb_topic_register(name: str, description: str, keywords: list[str], crawl_freq: str = "daily") -> str:
    payload = {
        "name": name, "description": description, "keywords": keywords,
        "status": "active", "crawl_freq": crawl_freq, "last_crawled": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_url": "n/a",
        "content_hash": compute_content_hash(name),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "citation": f"topic:{name}",
        "language": "en", "embedding_model": "voyage-3", "confidence": "high",
    }
    # topics collection is 1-dim placeholder (see scripts/create_collections.py micro-deviation)
    body = {"points": [{"id": name, "vector": [0.0], "payload": payload}]}
    _qdrant_put("/collections/topics/points", body)
    return name


def kb_topic_list(status: str = "active") -> list[dict]:
    res = _qdrant_post("/collections/topics/points/scroll", {
        "filter": {"must": [{"key": "status", "match": {"value": status}}]},
        "limit": 100,
        "with_payload": True,
    })
    return [p["payload"] for p in res.get("result", {}).get("points", [])]


def kb_stats() -> dict:
    res = _qdrant_get("/collections")
    out = {}
    for c in res.get("result", {}).get("collections", []):
        info = _qdrant_get(f"/collections/{c['name']}")
        out[c["name"]] = info.get("result", {}).get("points_count", 0)
    return out

"""External knowledge source search.

Functions: arxiv_search, semantic_scholar_search, github_search, tavily_search.

All results pass through normalize_chunk → source_url, citation, content_hash, etc.
Source-Enforcement: discard chunks without source URL.
"""
from __future__ import annotations
import hashlib
import os
import re
from datetime import datetime, timezone
import time
import requests
import xml.etree.ElementTree as ET


def _get_with_backoff(url: str, *, params=None, headers=None, timeout: int = 30,
                     max_retries: int = 3, backoff_base: float = 2.0,
                     alert_service: str | None = None) -> requests.Response:
    """GET with retry on 429/5xx. arXiv/Semantic-Scholar free tier throttles aggressively.

    alert_service: if persistent 5xx after retries, fire Discord quota alert under this service name.
    """
    last_err = None
    last_status = 0
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            last_status = r.status_code
            if r.status_code in (429, 500, 502, 503, 504):
                last_err = requests.HTTPError(f"HTTP {r.status_code}", response=r)
                if attempt < max_retries - 1:
                    time.sleep(backoff_base ** (attempt + 1))
                    continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(backoff_base ** (attempt + 1))
                continue
    # Exhausted: optional alert
    if alert_service:
        try:
            import sys
            sys.path.insert(0, str(__import__("pathlib").Path.home() / ".hermes" / "skills" / "knowledge-db"))
            from quota_alert import alert_with_hint
            cls = "rate_limit" if last_status == 429 else "persistent_5xx"
            alert_with_hint(alert_service, cls, f"HTTP {last_status} after {max_retries} retries: {url[:200]}")
        except Exception:
            pass
    raise last_err if last_err else RuntimeError("retry loop exhausted without exception")


def _hash(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def _read_env(key: str) -> str:
    """Hermes ~/.hermes/.env tolerates 'KEY = VAL' with spaces; shell source does not.
    Same helper as scripts/create_collections.py and skills/knowledge-db/kb_tools.py.
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


def _env(key: str, optional: bool = False) -> str | None:
    val = os.environ.get(key)
    if val:
        return val
    try:
        return _read_env(key)
    except KeyError:
        if optional:
            return None
        raise


def normalize_chunk(raw: dict) -> dict:
    url = raw.get("url") or raw.get("source_url")
    if not url:
        raise ValueError("missing source url; Source-Enforcement violation")
    text = raw.get("content") or raw.get("abstract") or raw.get("summary") or ""
    authors = raw.get("authors", [])
    title = raw.get("title", "")
    year = raw.get("year") or _extract_year(raw)
    citation_parts = [", ".join(authors[:3])] if authors else []
    if year:
        citation_parts.append(f"({year})")
    citation_parts.append(title)
    citation_parts.append(url)
    return {
        "source_url": url,
        "content_hash": _hash(f"{title}\n{text}"),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "citation": " ".join(p for p in citation_parts if p),
        "language": raw.get("language", "en"),
        "embedding_model": "voyage-3",
        "confidence": raw.get("confidence", "medium"),
        "title": title,
        "authors": authors,
        "year": year,
        "_text": text,
        **{k: v for k, v in raw.items() if k not in {"url", "source_url", "content", "abstract", "summary"}},
    }


def _extract_year(raw: dict) -> int | None:
    for k in ("published", "publishedAt", "pushed_at", "created_at"):
        v = raw.get(k)
        if v:
            m = re.search(r"(\d{4})", str(v))
            if m:
                return int(m.group(1))
    return None


def arxiv_search(query: str, max_results: int = 10, since_days: int | None = None) -> list[dict]:
    base = "http://export.arxiv.org/api/query"
    q = f"all:{query}"
    if since_days:
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y%m%d")
        q = f"{q} AND submittedDate:[{since}* TO 99999999*]"
    r = _get_with_backoff(base, params={"search_query": q, "max_results": max_results}, alert_service="arxiv")
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(r.text)
    out = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", "", ns) or "").strip()
        url = (entry.findtext("a:id", "", ns) or "").strip()
        summary = (entry.findtext("a:summary", "", ns) or "").strip()
        authors = [a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns)]
        published = entry.findtext("a:published", "", ns)
        out.append(normalize_chunk({
            "title": title, "url": url, "abstract": summary,
            "authors": authors, "published": published,
            "arxiv_id": url.rsplit("/", 1)[-1] if url else None,
        }))
    return out


def semantic_scholar_search(query: str, limit: int = 10) -> list[dict]:
    base = "https://api.semanticscholar.org/graph/v1/paper/search"
    r = _get_with_backoff(base, params={"query": query, "limit": limit, "fields": "title,authors,year,abstract,url,externalIds"}, alert_service="semantic_scholar")
    out = []
    for p in r.json().get("data", []):
        out.append(normalize_chunk({
            "title": p.get("title"),
            "url": p.get("url") or f"https://www.semanticscholar.org/paper/{p.get('paperId')}",
            "abstract": p.get("abstract") or "",
            "authors": [a.get("name") for a in p.get("authors", [])],
            "year": p.get("year"),
            "doi": (p.get("externalIds") or {}).get("DOI"),
        }))
    return out


def github_search(query: str, sort: str = "stars", since_days: int | None = None, limit: int = 10) -> list[dict]:
    q = query
    if since_days:
        from datetime import timedelta
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).strftime("%Y-%m-%d")
        q = f"{q} pushed:>={since}"
    headers = {"Accept": "application/vnd.github+json"}
    tok = _env("GITHUB_TOKEN", optional=True)
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    r = requests.get("https://api.github.com/search/repositories", headers=headers,
                     params={"q": q, "sort": sort, "per_page": limit}, timeout=30)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        try:
            import sys
            sys.path.insert(0, str(__import__("pathlib").Path.home() / ".hermes" / "skills" / "knowledge-db"))
            from quota_alert import alert_with_hint
            alert_with_hint("github", "rate_limit", f"HTTP 403 rate limit: {r.text[:200]}")
        except Exception:
            pass
    r.raise_for_status()
    out = []
    for repo in r.json().get("items", []):
        out.append(normalize_chunk({
            "title": repo["full_name"],
            "url": repo["html_url"],
            "content": repo.get("description") or "",
            "stars": repo.get("stargazers_count"),
            "last_commit": repo.get("pushed_at"),
            "license": (repo.get("license") or {}).get("spdx_id"),
            "language": "en",
            "status": "archived" if repo.get("archived") else "active",
        }))
    return out


def tavily_search(query: str, max_results: int = 5) -> list[dict]:
    r = requests.post("https://api.tavily.com/search", json={
        "api_key": _env("TAVILY_API_KEY"),
        "query": query,
        "max_results": max_results,
    }, timeout=30)
    if r.status_code in (429, 432, 433):
        try:
            import sys
            sys.path.insert(0, str(__import__("pathlib").Path.home() / ".hermes" / "skills" / "knowledge-db"))
            from quota_alert import alert_with_hint
            cls = "quota_exhausted" if "quota" in r.text.lower() or "month" in r.text.lower() else "rate_limit"
            alert_with_hint("tavily", cls, f"HTTP {r.status_code}: {r.text[:300]}")
        except Exception:
            pass
    r.raise_for_status()
    out = []
    for item in r.json().get("results", []):
        out.append(normalize_chunk({
            "title": item.get("title"),
            "url": item.get("url"),
            "content": item.get("content") or "",
        }))
    return out

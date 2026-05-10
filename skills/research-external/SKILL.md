---
name: research-external
description: External knowledge source search (arXiv, Semantic Scholar, GitHub, Tavily, Patent, archive.org Wayback, PDF extract). Used by R&D Engineers A and B in both reactive and cron modes. Every result MUST carry source_url, citation, content_hash before upsert.
---

# research-external

External search for the Continuous Researcher. All results pass through Source-Enforcement: discard chunks without source URL/DOI. Use with knowledge-db for upsert.

Functions: arxiv_search, semantic_scholar_search, github_search, tavily_search, patent_search, archive_wayback, pdf_extract. See external_tools.py.

API keys (loaded from ~/.hermes/.env): TAVILY_API_KEY, GITHUB_TOKEN, SERPAPI_KEY (optional).

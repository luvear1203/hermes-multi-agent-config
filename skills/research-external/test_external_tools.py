"""Tests for external_tools.py — Plan Task 16 Step 2."""
import pytest
from unittest.mock import patch, MagicMock
from external_tools import arxiv_search, normalize_chunk


def test_normalize_chunk_requires_source():
    with pytest.raises(ValueError):
        normalize_chunk({"title": "T"})


def test_normalize_chunk_produces_required_fields():
    c = normalize_chunk({"title": "T", "url": "https://x", "content": "abstract", "authors": ["A"]})
    assert c["source_url"] == "https://x"
    assert "citation" in c
    assert c["language"] == "en"


def test_arxiv_search_invokes_api():
    sample = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Paper</title>
    <id>http://arxiv.org/abs/2401.00001</id>
    <summary>abstract</summary>
    <author><name>Smith</name></author>
    <published>2024-01-01T00:00:00Z</published>
  </entry>
</feed>'''
    with patch("external_tools.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = sample
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        results = arxiv_search("mpm physics", max_results=1)
        assert len(results) == 1
        assert "arxiv.org" in results[0]["source_url"]

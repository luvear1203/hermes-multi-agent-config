"""Tests for kb_tools.py — Plan Task 15 Step 1."""
import pytest
from unittest.mock import patch
from kb_tools import compute_content_hash, validate_payload, kb_upsert


def test_compute_content_hash_stable():
    h1 = compute_content_hash("hello world")
    h2 = compute_content_hash("hello world")
    assert h1 == h2 and h1.startswith("sha256:")


def test_validate_payload_requires_source_url():
    bad = {"content_hash": "x", "retrieved_at": "2026-05-10", "citation": "c"}
    with pytest.raises(ValueError, match="source_url"):
        validate_payload(bad)


def test_validate_payload_passes_complete():
    good = {
        "source_url": "https://arxiv.org/abs/2401.00001",
        "content_hash": "sha256:abc",
        "retrieved_at": "2026-05-10T12:00:00Z",
        "citation": "Smith 2026",
        "language": "en",
        "embedding_model": "voyage-3",
        "confidence": "high",
    }
    validate_payload(good)  # no raise


def test_kb_upsert_dedupes_on_content_hash():
    with patch("kb_tools._qdrant_get") as mock_get, patch("kb_tools._qdrant_put") as mock_put:
        mock_get.return_value = {"result": {"id": "existing", "payload": {}}}
        result = kb_upsert("kb_papers", text="x", payload={
            "source_url": "u", "content_hash": "sha256:x", "retrieved_at": "t",
            "citation": "c", "language": "en", "embedding_model": "voyage-3", "confidence": "high",
        })
        assert result == "skipped_dedupe"
        mock_put.assert_not_called()

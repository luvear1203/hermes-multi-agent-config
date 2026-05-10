"""Tests for create_collections.py — Plan Task 14 Step 2."""
import pytest
from create_collections import COLLECTIONS, build_create_request


def test_collections_count():
    assert len(COLLECTIONS) == 12


def test_collections_names():
    expected = {
        "wiki_entities", "wiki_concepts", "wiki_architecture",
        "kb_papers", "kb_oss_projects", "kb_industry_solutions",
        "kb_lessons_learned", "kb_dev_docs",
        "mythrill_code", "chat_memory", "personal_notes", "topics",
    }
    assert {c["name"] for c in COLLECTIONS} == expected


def test_build_create_request_voyage_dim():
    req = build_create_request("wiki_entities")
    assert req["vectors"]["size"] == 1024
    assert req["vectors"]["distance"] == "Cosine"


def test_topics_collection_uses_placeholder_dim():
    req = build_create_request("topics")
    # Qdrant rejects size=0 — use 1-dim placeholder. Queries rely on payload filter, not similarity.
    assert req["vectors"]["size"] == 1

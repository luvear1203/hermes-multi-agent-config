"""Tests for scripts/audit_wiki.py — wiki page classification."""
from pathlib import Path

import pytest

from audit_wiki import classify_page, audit_wiki


def test_classify_handoff_as_compress():
    page = Path("docs/handoff/llm1-validation-2026-05-06.md")
    assert classify_page(page, content="...verification report...") == "compress"


def test_classify_architecture_as_preserve():
    page = Path("architecture/roles.md")
    assert classify_page(page, content="...role table...") == "preserve"


def test_classify_ip_as_preserve():
    page = Path("entities/c-chasm-ip-core.md")
    assert classify_page(page, content="...cosmology SoT...") == "preserve"


def test_classify_unknown_as_review():
    page = Path("entities/some-random-entity.md")
    assert classify_page(page, content="...unknown...") == "review"


def test_audit_returns_categorized_report(tmp_path):
    # Create minimal wiki tree
    (tmp_path / "architecture").mkdir()
    (tmp_path / "architecture" / "roles.md").write_text("# Roles")
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts" / "mythrill-architecture.md").write_text("# Mythrill")
    (tmp_path / "entities").mkdir()
    (tmp_path / "entities" / "ai-rookie-2026.md").write_text("# AI Rookie")
    report = audit_wiki(tmp_path)
    assert set(report.keys()) == {"preserve", "compress", "review"}
    assert any("roles.md" in p["path"] for p in report["preserve"])
    assert any("mythrill-architecture" in p["path"] for p in report["preserve"])
    assert any("ai-rookie-2026" in p["path"] for p in report["review"])

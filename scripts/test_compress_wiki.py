"""Tests for compress_wiki.py — Plan Task 26 Step 1."""
from pathlib import Path
from compress_wiki import compress_page


def test_compress_keeps_frontmatter(tmp_path):
    src = tmp_path / "page.md"
    src.write_text("---\ntitle: Test\nupdated: 2026-04-01\n---\n# Body\n\nlong content " * 200)
    out = compress_page(src, content=src.read_text())
    assert out.startswith("---\n")
    assert "title: Test" in out
    assert "updated: 2026-05-10" in out
    assert "원본 보존:" in out


def test_compress_extracts_summary(tmp_path):
    text = "# Hdr\n\nFirst para is the summary.\n\nMore detail.\n"
    out = compress_page(tmp_path / "p.md", content=text)
    assert "First para is the summary" in out

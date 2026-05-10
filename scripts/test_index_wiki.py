"""Tests for index_wiki.py — Plan Task 17 Step 1."""
from pathlib import Path
from index_wiki import route_collection


def test_route_entities():
    assert route_collection(Path("entities/mythrill-pipeline.md")) == "wiki_entities"


def test_route_concepts():
    assert route_collection(Path("concepts/mpm-constitutive-equation-swap.md")) == "wiki_concepts"


def test_route_architecture():
    assert route_collection(Path("architecture/roles.md")) == "wiki_architecture"


def test_route_unknown_returns_none():
    assert route_collection(Path("raw/something.md")) is None

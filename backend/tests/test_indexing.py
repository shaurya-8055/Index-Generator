"""Unit tests for the indexing engine (extraction, normalization, mapping, format)."""
from __future__ import annotations

from app.indexing.formatter import format_index, format_index_text
from app.indexing.normalizer import normalize_topics
from app.indexing.page_mapper import map_topics_to_pages
from app.indexing.text_utils import normalize_topic_label, topic_key
from app.llm.extractor import extract_topics


def test_normalize_topic_label_preserves_acronyms():
    assert normalize_topic_label("graph algorithms") == "Graph Algorithms"
    assert normalize_topic_label("bfs") == "BFS"
    assert normalize_topic_label("  binary   trees ") == "Binary Trees"


def test_topic_key_merges_plurals():
    assert topic_key("Binary Tree") == topic_key("Binary Trees")


def test_normalize_topics_groups_variants():
    result = normalize_topics(["Binary Tree", "Binary Trees", "Arrays"])
    # Plural canonical chosen; both variants grouped.
    assert "Binary Trees" in result
    assert set(result["Binary Trees"]) == {"Binary Tree", "Binary Trees"}
    assert "Arrays" in result


def test_extract_topics_heuristic():
    text = (
        "Arrays are data structures. Arrays store elements. "
        "Graph algorithms use BFS. Graph algorithms matter."
    )
    topics = extract_topics(text)
    lowered = {t.lower() for t in topics}
    assert any("array" in t for t in lowered)
    assert any("graph" in t for t in lowered)


def test_map_topics_to_pages_dedupes_and_sorts():
    normalized = {"Arrays": ["Arrays"], "Graphs": ["Graphs"]}
    pages = {1: "arrays here", 2: "graphs and arrays", 3: "nothing relevant"}
    mapping = map_topics_to_pages(normalized, pages)
    assert mapping["Arrays"] == [1, 2]
    assert mapping["Graphs"] == [2]


def test_format_index_groups_alphabetically():
    topic_pages = {"Arrays": [1, 2], "Binary Trees": [3], "Graphs": [4]}
    index = format_index(topic_pages)
    letters = [g["letter"] for g in index["groups"]]
    assert letters == ["A", "B", "G"]
    assert index["total_topics"] == 3
    assert index["total_pages_referenced"] == 4

    text = format_index_text(index)
    assert "Arrays" in text and "1, 2" in text

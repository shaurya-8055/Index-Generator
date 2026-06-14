"""Integration test for the LangGraph index pipeline (heuristic mode)."""
from __future__ import annotations

from app.graph.workflow import run_index_pipeline


def test_pipeline_end_to_end(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text(
        "Arrays are data structures. Arrays store elements.\f"
        "Graph algorithms use BFS and DFS. Binary trees support search.",
        encoding="utf-8",
    )
    state = run_index_pipeline(str(f))

    assert state.get("errors") == []
    assert state["page_count"] == 2
    assert state["topics"], "expected some topics"
    assert "groups" in state["index"]
    assert state["index"]["total_topics"] > 0
    assert state["index_text"].strip()

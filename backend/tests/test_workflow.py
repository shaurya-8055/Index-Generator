"""Integration test for the LangGraph index pipeline (heuristic mode)."""
from __future__ import annotations

from app.graph.state import IndexState
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


def test_node_outputs_are_declared_in_state(tmp_path):
    """LangGraph's StateGraph drops keys not declared in IndexState. Every key a
    node returns must therefore exist in the schema, or it silently vanishes
    between nodes (this is what once produced empty indexes)."""
    from app.graph import nodes

    declared = set(IndexState.__annotations__)

    f = tmp_path / "doc.txt"
    f.write_text("Arrays store data. Graphs use BFS. Arrays matter.", encoding="utf-8")

    state: dict = {"file_path": str(f), "max_topics_per_chunk": 40}
    for node in (
        nodes.document_loader_node,
        nodes.chunking_node,
        nodes.topic_extraction_node,
        nodes.normalization_node,
        nodes.page_mapping_node,
        nodes.index_formatter_node,
    ):
        out = node(state)
        undeclared = set(out) - declared
        assert not undeclared, f"{node.__name__} returns undeclared keys: {undeclared}"
        state.update(out)

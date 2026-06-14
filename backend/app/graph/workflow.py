"""Assemble the index-generation pipeline as a LangGraph ``StateGraph``.

Graph flow::

    Document Loader -> Chunking -> Topic Extraction -> Normalization
        -> Page Mapping -> Index Formatter -> END

When LangGraph is not installed the same nodes run via a plain sequential
fallback so the pipeline always works.
"""
from __future__ import annotations

import logging

from app.graph.nodes import (
    chunking_node,
    document_loader_node,
    index_formatter_node,
    normalization_node,
    page_mapping_node,
    topic_extraction_node,
)
from app.graph.state import IndexState

logger = logging.getLogger(__name__)

_NODE_SEQUENCE = [
    ("document_loader", document_loader_node),
    ("chunking", chunking_node),
    ("topic_extraction", topic_extraction_node),
    ("normalization", normalization_node),
    ("page_mapping", page_mapping_node),
    ("index_formatter", index_formatter_node),
]


def build_workflow():
    """Compile and return a LangGraph workflow, or ``None`` if unavailable."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError:  # pragma: no cover - fallback path
        logger.warning("LangGraph not installed; sequential runner will be used.")
        return None

    graph = StateGraph(IndexState)
    for name, fn in _NODE_SEQUENCE:
        graph.add_node(name, fn)

    graph.add_edge(START, _NODE_SEQUENCE[0][0])
    for (name, _), (next_name, _) in zip(_NODE_SEQUENCE, _NODE_SEQUENCE[1:]):
        graph.add_edge(name, next_name)
    graph.add_edge(_NODE_SEQUENCE[-1][0], END)

    return graph.compile()


def run_index_pipeline(
    file_path: str,
    *,
    enable_ocr: bool = False,
    max_topics_per_chunk: int = 40,
) -> IndexState:
    """Run the full pipeline for one document and return the final state."""
    initial: IndexState = {
        "file_path": file_path,
        "enable_ocr": enable_ocr,
        "max_topics_per_chunk": max_topics_per_chunk,
        "errors": [],
    }

    workflow = build_workflow()
    if workflow is not None:
        return workflow.invoke(initial)
    return _run_sequential(initial)


def _run_sequential(state: IndexState) -> IndexState:
    current = dict(state)
    for name, fn in _NODE_SEQUENCE:
        try:
            current.update(fn(current))
        except Exception as exc:
            logger.exception("Node %s failed", name)
            current.setdefault("errors", []).append(f"{name}: {exc}")
            break
    return current  # type: ignore[return-value]

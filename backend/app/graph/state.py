"""Shared state object flowing through the LangGraph workflow."""
from __future__ import annotations

from typing import TypedDict


class IndexState(TypedDict, total=False):
    # Inputs
    file_path: str
    enable_ocr: bool
    max_topics_per_chunk: int

    # Node outputs
    pages: dict[int, str]
    chunks: list[dict]  # [{"page": int, "text": str}, ...]
    topics: list[str]
    normalized_topics: dict[str, list[str]]  # canonical -> [variants]
    topic_pages: dict[str, list[int]]  # canonical -> [page numbers]
    index: dict
    index_text: str
    exported_files: list[str]

    # Diagnostics
    page_count: int
    used_ocr: bool
    errors: list[str]

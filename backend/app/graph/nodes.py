"""Workflow node implementations.

Each node is a pure function ``IndexState -> partial IndexState`` so it can be
used both inside LangGraph and in a plain sequential runner / unit tests.
"""
from __future__ import annotations

import logging

from app.config import settings
from app.indexing.formatter import format_index, format_index_text
from app.indexing.page_mapper import map_topics_to_pages
from app.llm.extractor import extract_topics
from app.llm.normalizer_llm import llm_normalize_topics
from app.parsing.loader import load_document

logger = logging.getLogger(__name__)


def document_loader_node(state: dict) -> dict:
    """Node 1 — parse the uploaded file into a {page: text} map."""
    doc = load_document(state["file_path"], enable_ocr=state.get("enable_ocr", False))
    return {
        "pages": doc.pages,
        "page_count": doc.page_count,
        "used_ocr": doc.used_ocr,
    }


def chunking_node(state: dict) -> dict:
    """Node 2 — split large pages into chunks (RecursiveCharacterTextSplitter)."""
    pages: dict[int, str] = state.get("pages", {})
    splitter = _get_splitter()
    chunks: list[dict] = []
    for page_no, text in pages.items():
        if not text or not text.strip():
            continue
        for piece in splitter(text):
            chunks.append({"page": page_no, "text": piece})
    return {"chunks": chunks}


def topic_extraction_node(state: dict) -> dict:
    """Node 3 — extract topics from each chunk via LLM (or heuristic)."""
    chunks: list[dict] = state.get("chunks", [])
    max_topics = state.get("max_topics_per_chunk", 40)
    seen: set[str] = set()
    topics: list[str] = []
    for chunk in chunks:
        for topic in extract_topics(chunk["text"], max_topics=max_topics):
            if topic.lower() not in seen:
                seen.add(topic.lower())
                topics.append(topic)
    return {"topics": topics}


def normalization_node(state: dict) -> dict:
    """Node 4 — merge synonyms / plurals / abbreviations into canonical labels."""
    return {"normalized_topics": llm_normalize_topics(state.get("topics", []))}


def page_mapping_node(state: dict) -> dict:
    """Node 5 — map each canonical topic to the pages where it appears."""
    topic_pages = map_topics_to_pages(
        state.get("normalized_topics", {}),
        state.get("pages", {}),
    )
    return {"_topic_pages": topic_pages}


def index_formatter_node(state: dict) -> dict:
    """Node 6 — build the alphabetical, grouped index structure + text."""
    topic_pages = state.get("_topic_pages", {})
    index = format_index(topic_pages)
    return {"index": index, "index_text": format_index_text(index)}


def _get_splitter():
    """Return a callable ``str -> list[str]`` using LangChain's splitter when
    available, else a simple length-based splitter."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        rc = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        return rc.split_text
    except ImportError:  # pragma: no cover - fallback path

        def _simple(text: str) -> list[str]:
            size, overlap = settings.chunk_size, settings.chunk_overlap
            if len(text) <= size:
                return [text]
            out, start = [], 0
            while start < len(text):
                out.append(text[start : start + size])
                start += size - overlap
            return out

        return _simple

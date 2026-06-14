"""Run the LangGraph pipeline for a document and persist the resulting index."""
from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.graph.workflow import run_index_pipeline
from app.models import Document, DocumentStatus, Index, Topic

logger = logging.getLogger(__name__)


def generate_index_for_document(
    db: Session, document: Document, *, enable_ocr: bool = False
) -> Index:
    """Execute the workflow and store a new versioned Index for the document."""
    document.status = DocumentStatus.processing
    db.commit()

    try:
        state = run_index_pipeline(document.file_path, enable_ocr=enable_ocr)
    except Exception as exc:
        document.status = DocumentStatus.failed
        document.error = str(exc)
        db.commit()
        logger.exception("Index generation failed for document %s", document.id)
        raise

    if state.get("errors"):
        document.status = DocumentStatus.failed
        document.error = "; ".join(state["errors"])
        db.commit()
        raise RuntimeError(document.error)

    index_data = state.get("index", {"groups": [], "total_topics": 0, "total_pages_referenced": 0})
    index_text = state.get("index_text", "")

    next_version = (
        db.query(Index).filter(Index.document_id == document.id).count() + 1
    )
    index = Index(
        document_id=document.id,
        version=next_version,
        index_json=json.dumps(index_data),
        index_text=index_text,
    )
    db.add(index)
    db.flush()  # assign index.id

    for group in index_data.get("groups", []):
        for entry in group["entries"]:
            db.add(
                Topic(
                    index_id=index.id,
                    name=entry["topic"],
                    pages=", ".join(str(p) for p in entry["pages"]),
                    frequency=len(entry["pages"]),
                )
            )

    document.page_count = state.get("page_count", document.page_count)
    document.status = DocumentStatus.completed
    document.error = None
    db.commit()
    db.refresh(index)
    return index


def search_index(index: Index, query: str) -> list[dict]:
    """Case-insensitive substring search over an index's topics."""
    data = json.loads(index.index_json)
    q = query.strip().lower()
    if not q:
        return []
    results: list[dict] = []
    for group in data.get("groups", []):
        for entry in group["entries"]:
            if q in entry["topic"].lower():
                results.append({"topic": entry["topic"], "pages": entry["pages"]})
    return results

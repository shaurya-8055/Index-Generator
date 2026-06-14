"""Index generation, retrieval, history, search and export endpoints."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database import get_db
from app.export.exporters import EXPORT_FORMATS, export_index
from app.models import Document, Index, User
from app.schemas import (
    GenerateIndexRequest,
    IndexOut,
    SearchResponse,
    SearchResult,
)
from app.services.index_service import generate_index_for_document, search_index

router = APIRouter(tags=["index"])


@router.post("/generate-index", response_model=IndexOut, status_code=status.HTTP_201_CREATED)
def generate_index(
    payload: GenerateIndexRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IndexOut:
    document = _get_owned_document(db, payload.document_id, current_user)
    try:
        index = generate_index_for_document(db, document, enable_ocr=payload.enable_ocr)
    except Exception as exc:  # noqa: BLE001 - surfaced as 500 with detail
        raise HTTPException(status_code=500, detail=f"Index generation failed: {exc}")
    return _to_index_out(index)


@router.get("/index/{index_id}", response_model=IndexOut)
def get_index(
    index_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IndexOut:
    index = _get_owned_index(db, index_id, current_user)
    return _to_index_out(index)


@router.get("/history", response_model=list[IndexOut])
def history(
    document_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[IndexOut]:
    query = (
        db.query(Index)
        .join(Document, Index.document_id == Document.id)
        .filter(Document.user_id == current_user.id)
    )
    if document_id is not None:
        query = query.filter(Index.document_id == document_id)
    indexes = query.order_by(Index.created_at.desc()).all()
    return [_to_index_out(i) for i in indexes]


@router.get("/index/{index_id}/search", response_model=SearchResponse)
def search(
    index_id: int,
    q: str = Query(..., min_length=1, description="Topic search query"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    index = _get_owned_index(db, index_id, current_user)
    results = search_index(index, q)
    return SearchResponse(
        query=q,
        results=[SearchResult(**r) for r in results],
    )


@router.get("/export/{fmt}/{index_id}")
def export(
    fmt: str,
    index_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    if fmt.lower() not in EXPORT_FORMATS:
        raise HTTPException(
            status_code=400, detail=f"Unsupported format. Use one of {EXPORT_FORMATS}."
        )
    index = _get_owned_index(db, index_id, current_user)
    data = json.loads(index.index_json)
    content, media_type, file_ext = export_index(data, fmt)
    filename = f"index_{index_id}_v{index.version}.{file_ext}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _to_index_out(index: Index) -> IndexOut:
    return IndexOut(
        id=index.id,
        document_id=index.document_id,
        version=index.version,
        index=json.loads(index.index_json),
        index_text=index.index_text,
        created_at=index.created_at,
    )


def _get_owned_document(db: Session, document_id: int, user: User) -> Document:
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def _get_owned_index(db: Session, index_id: int, user: User) -> Index:
    index = db.get(Index, index_id)
    if not index:
        raise HTTPException(status_code=404, detail="Index not found")
    document = db.get(Document, index.document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Index not found")
    return index

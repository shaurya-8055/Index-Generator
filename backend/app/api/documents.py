"""Document upload and listing endpoints."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Document, DocumentStatus, User
from app.parsing.loader import SUPPORTED_EXTENSIONS
from app.schemas import DocumentOut

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentOut:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_bytes // (1024*1024)} MB",
        )
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = settings.storage_dir / stored_name
    dest.write_bytes(contents)

    document = Document(
        user_id=current_user.id,
        filename=file.filename or stored_name,
        file_path=str(dest),
        status=DocumentStatus.uploaded,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return DocumentOut.model_validate(document)


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentOut]:
    docs = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [DocumentOut.model_validate(d) for d in docs]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    document = _get_owned_document(db, document_id, current_user)
    # Best-effort removal of the stored file.
    try:
        Path(document.file_path).unlink(missing_ok=True)
    except OSError:
        pass
    db.delete(document)
    db.commit()


def _get_owned_document(db: Session, document_id: int, user: User) -> Document:
    document = db.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

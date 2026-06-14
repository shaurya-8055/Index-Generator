"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---- Auth ----
class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- Documents ----
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    page_count: int
    status: str
    error: str | None = None
    created_at: datetime


# ---- Index ----
class IndexEntry(BaseModel):
    topic: str
    pages: list[int]


class IndexGroup(BaseModel):
    letter: str
    entries: list[IndexEntry]


class IndexData(BaseModel):
    groups: list[IndexGroup]
    total_topics: int
    total_pages_referenced: int


class IndexOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    version: int
    index: IndexData
    index_text: str
    created_at: datetime


class GenerateIndexRequest(BaseModel):
    document_id: int
    enable_ocr: bool = False


class SearchResult(BaseModel):
    topic: str
    pages: list[int]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]

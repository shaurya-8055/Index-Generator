"""Unit tests for document parsing."""
from __future__ import annotations

import pytest

from app.parsing.loader import (
    UnsupportedFileTypeError,
    load_document,
)


def test_load_txt(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("Hello world.\n\nSecond paragraph.", encoding="utf-8")
    doc = load_document(f)
    assert doc.page_count >= 1
    assert "Hello world" in doc.pages[1]


def test_load_text_with_formfeed_pagination(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("Page one text\fPage two text", encoding="utf-8")
    doc = load_document(f)
    assert doc.page_count == 2
    assert "one" in doc.pages[1]
    assert "two" in doc.pages[2]


def test_unsupported_type(tmp_path):
    f = tmp_path / "doc.xyz"
    f.write_text("data", encoding="utf-8")
    with pytest.raises(UnsupportedFileTypeError):
        load_document(f)


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_document("does-not-exist.txt")

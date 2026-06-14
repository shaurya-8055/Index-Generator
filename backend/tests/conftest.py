"""Shared pytest fixtures: isolated SQLite DB and an authenticated test client."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Configure an isolated database + storage BEFORE importing the app/settings.
_TMP = Path(tempfile.mkdtemp(prefix="idxgen_test_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["STORAGE_DIR"] = str(_TMP / "storage")
os.environ["LLM_PROVIDER"] = "fallback"


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    creds = {"name": "Tester", "email": "tester@example.com", "password": "secret1"}
    resp = client.post("/api/auth/register", json=creds)
    if resp.status_code == 400:  # already registered in a prior test
        resp = client.post(
            "/api/auth/login",
            data={"username": creds["email"], "password": creds["password"]},
        )
    assert resp.status_code in (200, 201), resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_text() -> bytes:
    return (
        b"Arrays are fundamental data structures. Arrays store elements contiguously. "
        b"Graph algorithms use BFS and DFS to traverse graphs. "
        b"Binary trees are hierarchical data structures. Binary trees support fast search. "
        b"Sorting algorithms organize arrays. Sorting algorithms include quicksort."
    )

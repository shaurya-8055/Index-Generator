"""Integration tests for the FastAPI endpoints."""
from __future__ import annotations

import io


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login(client):
    r = client.post(
        "/api/auth/register",
        json={"name": "Bob", "email": "bob@example.com", "password": "secret1"},
    )
    assert r.status_code == 201
    r = client.post(
        "/api/auth/login",
        data={"username": "bob@example.com", "password": "secret1"},
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_requires_auth(client):
    assert client.get("/api/documents").status_code == 401


def test_full_index_flow(client, auth_headers, sample_text):
    up = client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("sample.txt", io.BytesIO(sample_text), "text/plain")},
    )
    assert up.status_code == 201, up.text
    doc_id = up.json()["id"]

    gen = client.post(
        "/api/generate-index", headers=auth_headers, json={"document_id": doc_id}
    )
    assert gen.status_code == 201, gen.text
    index = gen.json()
    assert index["index"]["total_topics"] > 0

    iid = index["id"]
    got = client.get(f"/api/index/{iid}", headers=auth_headers)
    assert got.status_code == 200

    search = client.get(
        f"/api/index/{iid}/search", headers=auth_headers, params={"q": "array"}
    )
    assert search.status_code == 200
    assert any("array" in r["topic"].lower() for r in search.json()["results"])

    for fmt in ("json", "csv", "markdown", "pdf"):
        exp = client.get(f"/api/export/{fmt}/{iid}", headers=auth_headers)
        assert exp.status_code == 200, fmt

    hist = client.get("/api/history", headers=auth_headers)
    assert hist.status_code == 200
    assert len(hist.json()) >= 1


def test_reject_unsupported_upload(client, auth_headers):
    bad = client.post(
        "/api/documents/upload",
        headers=auth_headers,
        files={"file": ("bad.exe", io.BytesIO(b"x"), "application/octet-stream")},
    )
    assert bad.status_code == 400

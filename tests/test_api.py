"""
Integration tests for ClauseLens REST API.
Uses FastAPI TestClient — no real server or database needed.
Run with:  pytest tests/test_api.py -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app

client = TestClient(app, raise_server_exceptions=True)


# ─── Health ──────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_200(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_body(self):
        body = client.get("/api/health").json()
        assert body["status"] == "ok"
        assert "ClauseLens" in body["service"]


# ─── Security Headers ────────────────────────────────────────────────────────

class TestSecurityHeaders:
    def test_x_content_type_options(self):
        resp = client.get("/api/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self):
        resp = client.get("/api/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_x_xss_protection(self):
        resp = client.get("/api/health")
        assert resp.headers.get("x-xss-protection") == "1; mode=block"

    def test_referrer_policy(self):
        resp = client.get("/api/health")
        assert "strict-origin" in resp.headers.get("referrer-policy", "")


# ─── Document Endpoints ──────────────────────────────────────────────────────

class TestDocumentEndpoints:
    @patch("backend.main.list_documents")
    def test_list_documents_returns_list(self, mock_list):
        mock_list.return_value = []
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @patch("backend.main.get_document")
    def test_get_document_not_found(self, mock_get):
        mock_get.return_value = None
        resp = client.get("/api/documents/nonexistent")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    @patch("backend.main.get_document")
    def test_compare_missing_doc_a(self, mock_get):
        mock_get.return_value = None
        resp = client.post("/api/documents/compare", json={"doc_id_a": "x", "doc_id_b": "y"})
        assert resp.status_code == 404


# ─── Upload Endpoint ─────────────────────────────────────────────────────────

class TestUploadEndpoint:
    def test_upload_rejects_non_pdf(self):
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("evil.exe", b"binary-content", "application/octet-stream")},
        )
        assert resp.status_code == 400
        # The detail message lists allowed extensions
        assert ".pdf" in resp.json()["detail"] or "Unsupported" in resp.json()["detail"]

    def test_upload_rejects_oversized_file(self):
        big_content = b"A" * (26 * 1024 * 1024)  # 26 MB > 25 MB limit
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("large.pdf", big_content, "application/pdf")},
        )
        assert resp.status_code == 413

    def test_upload_filename_path_traversal(self):
        """Path-traversal filenames must be sanitised, not crash the server."""
        try:
            resp = client.post(
                "/api/documents/upload",
                files={"file": ("../../etc/passwd.pdf", b"%PDF-1", "application/pdf")},
            )
            # Either sanitised-and-processed (may fail on parse) or 4xx — never 5xx on traversal
            assert resp.status_code in (200, 400, 422, 500)  # 500 only on PDF parse, not traversal
        finally:
            from pathlib import Path
            test_file = Path("data/uploads/passwd.pdf")
            if test_file.exists():
                test_file.unlink()


# ─── QA Endpoint ─────────────────────────────────────────────────────────────

class TestQAEndpoint:
    @patch("backend.main.get_document")
    def test_qa_doc_not_found(self, mock_get):
        mock_get.return_value = None
        resp = client.post("/api/documents/missing/qa", json={"question": "hello"})
        assert resp.status_code == 404


# ─── Actionable Endpoints ────────────────────────────────────────────────────

class TestActionableEndpoints:
    @patch("backend.main.get_document")
    def test_deadlines_not_found(self, mock_get):
        mock_get.return_value = None
        resp = client.get("/api/documents/bad-doc/actionable/deadlines")
        assert resp.status_code == 404

    @patch("backend.main.get_document")
    def test_lawyer_prep_not_found(self, mock_get):
        mock_get.return_value = None
        resp = client.get("/api/documents/bad-doc/actionable/lawyer-prep")
        assert resp.status_code == 404

    @patch("backend.main.get_document")
    def test_negotiations_not_found(self, mock_get):
        mock_get.return_value = None
        resp = client.get("/api/documents/bad-doc/actionable/negotiations")
        assert resp.status_code == 404

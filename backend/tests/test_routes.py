import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestChat:
    def test_chat_returns_response(self):
        resp = client.post("/api/chat", json={"message": "What is AAPL?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert len(data["response"]) > 0

    def test_chat_with_session(self):
        resp = client.post(
            "/api/chat",
            json={"message": "Hello", "session_id": "test-session-route"},
        )
        assert resp.status_code == 200


class TestIngest:
    def test_rejects_non_pdf(self):
        resp = client.post(
            "/api/ingest",
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        assert resp.status_code == 400
        assert "PDF" in resp.json()["detail"]

    def test_rejects_large_file(self):
        resp = client.post(
            "/api/ingest",
            files={"file": ("large.pdf", b"x" * (10 * 1024 * 1024 + 1), "application/pdf")},
        )
        assert resp.status_code == 400
        assert "10 MB" in resp.json()["detail"]

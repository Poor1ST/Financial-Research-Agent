import pytest


def register_user(client, username="tester", email="t@test.com", password="secret123"):
    return client.post("/api/auth/register", json={"username": username, "email": email, "password": password}).json()


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestChart:
    def test_chart_valid_ticker(self, client):
        resp = client.get("/api/chart?ticker=AAPL&period=1mo")
        if resp.status_code == 500:
            pytest.skip(f"yfinance error: {resp.json()}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "chart_data"
        assert data["ticker"] == "AAPL"
        assert len(data["data"]) > 0

    def test_chart_invalid_ticker(self, client):
        resp = client.get("/api/chart?ticker=ZZZZZZ")
        assert resp.status_code == 404

    def test_chart_missing_ticker(self, client):
        resp = client.get("/api/chart")
        assert resp.status_code == 422

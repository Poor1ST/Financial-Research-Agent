import pytest


class TestRegister:
    def test_register_returns_token_and_user(self, client):
        body = {"username": "alice", "email": "alice@example.com", "password": "secret123"}
        resp = client.post("/api/auth/register", json=body)

        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20
        assert data["user"]["username"] == "alice"
        assert data["user"]["email"] == "alice@example.com"
        assert "id" in data["user"]

    def test_register_duplicate_username_rejected(self, client):
        body = {"username": "alice", "email": "alice@example.com", "password": "secret123"}
        client.post("/api/auth/register", json=body)
        resp = client.post("/api/auth/register", json=body)
        assert resp.status_code == 400

    def test_register_duplicate_email_rejected(self, client):
        client.post("/api/auth/register", json={"username": "alice", "email": "same@example.com", "password": "secret123"})
        resp = client.post("/api/auth/register", json={"username": "bob", "email": "same@example.com", "password": "secret123"})
        assert resp.status_code == 400


class TestLogin:
    def test_login_with_username_returns_token(self, client):
        client.post("/api/auth/register", json={"username": "alice", "email": "a@b.com", "password": "secret123"})
        resp = client.post("/api/auth/login", json={"username": "alice", "password": "secret123"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["username"] == "alice"
        assert len(data["access_token"]) > 20

    def test_login_with_email_returns_token(self, client):
        client.post("/api/auth/register", json={"username": "bob", "email": "bob@test.com", "password": "pass123"})
        resp = client.post("/api/auth/login", json={"username": "bob@test.com", "password": "pass123"})
        assert resp.status_code == 200

    def test_login_wrong_password_returns_401(self, client):
        client.post("/api/auth/register", json={"username": "alice", "email": "a@b.com", "password": "secret123"})
        resp = client.post("/api/auth/login", json={"username": "alice", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        resp = client.post("/api/auth/login", json={"username": "ghost", "password": "anything"})
        assert resp.status_code == 401


class TestAuthMiddleware:
    def test_me_without_token_returns_401(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalidtoken123"})
        assert resp.status_code == 401

    def test_me_with_valid_token_returns_user(self, client):
        reg = client.post("/api/auth/register", json={"username": "alice", "email": "a@b.com", "password": "secret123"}).json()
        token = reg["access_token"]
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "alice"

import pytest


def register_user(client, email="a@b.com", password="secret123"):
    return client.post("/api/auth/register", json={"email": email, "password": password}).json()


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


class TestCreateSession:
    def test_create_session_returns_new_chat(self, client):
        data = register_user(client)
        resp = client.post("/api/auth/sessions", headers=auth_header(data["access_token"]))
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "New Chat"
        assert len(body["id"]) > 10

    def test_create_session_without_auth_returns_401(self, client):
        resp = client.post("/api/auth/sessions")
        assert resp.status_code == 401


class TestListSessions:
    def test_list_sessions_returns_empty_list_initially(self, client):
        data = register_user(client)
        resp = client.get("/api/auth/sessions", headers=auth_header(data["access_token"]))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_sessions_returns_created_sessions(self, client):
        data = register_user(client)
        h = auth_header(data["access_token"])
        client.post("/api/auth/sessions", headers=h)
        client.post("/api/auth/sessions", headers=h)
        resp = client.get("/api/auth/sessions", headers=h)
        assert len(resp.json()) == 2

    def test_sessions_are_scoped_to_user(self, client):
        alice = register_user(client, "a@b.com")
        bob = register_user(client, "b@b.com", "pass456")
        client.post("/api/auth/sessions", headers=auth_header(alice["access_token"]))
        bob_sessions = client.get("/api/auth/sessions", headers=auth_header(bob["access_token"]))
        assert bob_sessions.json() == []


class TestDeleteSession:
    def test_delete_session_removes_it(self, client):
        data = register_user(client)
        h = auth_header(data["access_token"])
        s = client.post("/api/auth/sessions", headers=h).json()
        resp = client.delete(f"/api/auth/sessions/{s['id']}", headers=h)
        assert resp.status_code == 200
        assert len(client.get("/api/auth/sessions", headers=h).json()) == 0

    def test_delete_nonexistent_session_returns_404(self, client):
        data = register_user(client)
        resp = client.delete("/api/auth/sessions/nonexistent-id", headers=auth_header(data["access_token"]))
        assert resp.status_code == 404

    def test_cannot_delete_another_users_session(self, client):
        alice = register_user(client, "a@b.com")
        bob = register_user(client, "b@b.com", "pass456")
        s = client.post("/api/auth/sessions", headers=auth_header(alice["access_token"])).json()
        resp = client.delete(f"/api/auth/sessions/{s['id']}", headers=auth_header(bob["access_token"]))
        assert resp.status_code == 404


class TestSessionMessages:
    def test_get_messages_empty_initially(self, client):
        data = register_user(client)
        h = auth_header(data["access_token"])
        s = client.post("/api/auth/sessions", headers=h).json()
        resp = client.get(f"/api/auth/sessions/{s['id']}/messages", headers=h)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_messages_without_auth_returns_401(self, client):
        resp = client.get("/api/auth/sessions/some-id/messages")
        assert resp.status_code == 401

    def test_cannot_get_messages_of_another_user(self, client):
        alice = register_user(client, "a@b.com")
        bob = register_user(client, "b@b.com", "pass456")
        s = client.post("/api/auth/sessions", headers=auth_header(alice["access_token"])).json()
        resp = client.get(f"/api/auth/sessions/{s['id']}/messages", headers=auth_header(bob["access_token"]))
        assert resp.status_code == 404

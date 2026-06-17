import pytest


def register_user(client, username="alice", email="a@b.com", password="secret123"):
    return client.post("/api/auth/register", json={"username": username, "email": email, "password": password}).json()


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def create_session(client, token):
    return client.post("/api/auth/sessions", headers=auth_header(token)).json()


class TestChatAuth:
    def test_chat_without_token_returns_401(self, client):
        resp = client.post("/api/chat", json={"message": "hello", "session_id": "any"})
        assert resp.status_code == 401

    def test_chat_with_invalid_token_returns_401(self, client):
        resp = client.post("/api/chat", json={"message": "hello", "session_id": "any"},
                           headers={"Authorization": "Bearer invalid"})
        assert resp.status_code == 401


class TestChatSessionValidation:
    def test_chat_nonexistent_session_returns_404(self, client):
        data = register_user(client)
        resp = client.post("/api/chat", json={"message": "hello", "session_id": "nonexistent"},
                           headers=auth_header(data["access_token"]))
        assert resp.status_code == 404

    def test_cannot_chat_another_users_session(self, client):
        alice = register_user(client, "alice", "a@b.com")
        bob = register_user(client, "bob", "b@b.com", "pass456")
        alice_session = create_session(client, alice["access_token"])
        resp = client.post("/api/chat", json={"message": "hello", "session_id": alice_session["id"]},
                           headers=auth_header(bob["access_token"]))
        assert resp.status_code == 404


class TestChatFunctionality:
    def test_chat_returns_response(self, client):
        data = register_user(client)
        h = auth_header(data["access_token"])
        s = create_session(client, data["access_token"])
        resp = client.post("/api/chat", json={"message": "Say exactly: hello world", "session_id": s["id"]}, headers=h)
        assert resp.status_code == 200
        assert len(resp.json()["response"]) > 0

    def test_chat_saves_messages(self, client):
        data = register_user(client)
        h = auth_header(data["access_token"])
        s = create_session(client, data["access_token"])
        client.post("/api/chat", json={"message": "Say exactly: first message", "session_id": s["id"]}, headers=h)
        msgs = client.get(f"/api/auth/sessions/{s['id']}/messages", headers=h).json()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"
        assert msgs[0]["session_id"] == s["id"]

    def test_chat_auto_titles_session(self, client):
        data = register_user(client)
        h = auth_header(data["access_token"])
        s = create_session(client, data["access_token"])
        assert s["title"] == "New Chat"
        client.post("/api/chat", json={"message": "What is Apple stock price?", "session_id": s["id"]}, headers=h)
        updated = client.get("/api/auth/sessions", headers=h).json()
        assert updated[0]["title"] != "New Chat"
        assert "Apple" in updated[0]["title"] or "What" in updated[0]["title"]

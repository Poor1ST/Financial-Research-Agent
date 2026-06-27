import pytest


def register_user(client, email="a@b.com", password="secret123"):
    return client.post("/api/auth/register", json={"email": email, "password": password}).json()


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def create_session(client, token):
    return client.post("/api/auth/sessions", headers=auth_header(token)).json()


class TestChatAuth:
    def test_guest_can_chat_without_token(self, client):
        resp = client.post("/api/chat", json={"message": "Say exactly: hello world"})
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert len(data["response"]) > 0

    def test_chat_with_invalid_token_returns_200_for_guest(self, client):
        resp = client.post("/api/chat", json={"message": "Say exactly: hello world"},
                           headers={"Authorization": "Bearer invalid"})
        assert resp.status_code == 200
        assert len(resp.json()["response"]) > 0


class TestChatSessionValidation:
    def test_chat_nonexistent_session_returns_404(self, client):
        data = register_user(client)
        resp = client.post("/api/chat", json={"message": "hello", "session_id": "nonexistent"},
                           headers=auth_header(data["access_token"]))
        assert resp.status_code == 404

    def test_cannot_chat_another_users_session(self, client):
        alice = register_user(client, "a@b.com")
        bob = register_user(client, "b@b.com", "pass456")
        alice_session = create_session(client, alice["access_token"])
        resp = client.post("/api/chat", json={"message": "hello", "session_id": alice_session["id"]},
                           headers=auth_header(bob["access_token"]))
        assert resp.status_code == 404


class TestGuestChat:
    def test_guest_with_history_returns_200(self, client):
        resp = client.post("/api/chat", json={
            "message": "What is 2+2?",
            "history": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ]
        })
        assert resp.status_code == 200
        assert len(resp.json()["response"]) > 0

    def test_guest_without_session_id_works(self, client):
        resp = client.post("/api/chat", json={"message": "What is 2+2?"})
        assert resp.status_code == 200
        assert len(resp.json()["response"]) > 0

    def test_guest_message_not_in_any_session(self, client):
        client.post("/api/chat", json={"message": "What is 2+2?"})
        data = register_user(client)
        h = auth_header(data["access_token"])
        sessions = client.get("/api/auth/sessions", headers=h).json()
        assert len(sessions) == 0


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
        client.post("/api/chat", json={"message": "What is 2+2?", "session_id": s["id"]}, headers=h)
        updated = client.get("/api/auth/sessions", headers=h).json()
        assert updated[0]["title"] != "New Chat"

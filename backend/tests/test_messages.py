"""Tests for Phase 4 chat: REST endpoints + WebSocket."""

import pytest
from fastapi.testclient import TestClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _reg_login(client: TestClient, email: str, pw: str = "Chat1234!") -> str:
    client.post("/auth/register", json={"email": email, "password": pw})
    res = client.post("/auth/login", json={"email": email, "password": pw})
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _uid(client: TestClient, token: str) -> int:
    return client.get("/auth/me", headers=_auth(token)).json()["id"]


def _create_match(client: TestClient) -> tuple[str, str, int]:
    """Register two users, mutually like each other, return (token_a, token_b, match_id)."""
    ta = _reg_login(client, "chat_match_a@test.com")
    tb = _reg_login(client, "chat_match_b@test.com")
    a_id = _uid(client, ta)
    b_id = _uid(client, tb)
    client.post(f"/likes/{b_id}", headers=_auth(ta))
    res = client.post(f"/likes/{a_id}", headers=_auth(tb))
    match_id = res.json()["match_id"]
    return ta, tb, match_id


# ── REST: list messages ───────────────────────────────────────────────────────

class TestListMessages:
    def test_empty_initially(self, client: TestClient):
        ta, tb, match_id = _create_match(client)
        res = client.get(f"/messages/{match_id}", headers=_auth(ta))
        assert res.status_code == 200
        assert res.json()["items"] == []

    def test_requires_auth(self, client: TestClient):
        res = client.get("/messages/1")
        assert res.status_code == 401

    def test_non_member_rejected(self, client: TestClient):
        ta, tb, match_id = _create_match(client)
        tc = _reg_login(client, "chat_outsider@test.com")
        res = client.get(f"/messages/{match_id}", headers=_auth(tc))
        assert res.status_code == 403

    def test_invalid_match_id(self, client: TestClient):
        ta = _reg_login(client, "chat_nf@test.com")
        res = client.get("/messages/99999", headers=_auth(ta))
        assert res.status_code == 404


# ── REST: mark read ───────────────────────────────────────────────────────────

class TestMarkRead:
    def test_mark_read_empty(self, client: TestClient):
        ta, tb, match_id = _create_match(client)
        res = client.put(f"/messages/{match_id}/read", headers=_auth(ta))
        assert res.status_code == 200
        assert res.json()["marked_read"] == 0

    def test_requires_auth(self, client: TestClient):
        res = client.put("/messages/1/read")
        assert res.status_code == 401

    def test_non_member_rejected(self, client: TestClient):
        ta, tb, match_id = _create_match(client)
        tc = _reg_login(client, "chat_read_outsider@test.com")
        res = client.put(f"/messages/{match_id}/read", headers=_auth(tc))
        assert res.status_code == 403


# ── WebSocket ─────────────────────────────────────────────────────────────────

class TestChatWebSocket:
    def test_ws_invalid_token_rejected(self, client: TestClient):
        with client.websocket_connect("/ws/chat/1?token=bad_token") as ws:
            data = ws.receive_json()
            assert data["event"] == "error"
            assert data["code"] == "UNAUTHORIZED"

    def test_ws_connect_and_send(self, client: TestClient):
        ta, tb, match_id = _create_match(client)

        # Connect as User A
        with client.websocket_connect(f"/ws/chat/{match_id}?token={ta}") as ws_a:
            connected = ws_a.receive_json()
            assert connected["event"] == "connected"
            assert connected["match_id"] == match_id

            # Send a message
            ws_a.send_json({"content": "Hello from A!"})
            msg = ws_a.receive_json()
            assert msg["event"] == "message"
            assert msg["content"] == "Hello from A!"
            assert msg["sender_id"] == _uid(client, ta)
            assert "id" in msg
            assert "created_at" in msg

    def test_ws_persists_to_db(self, client: TestClient):
        ta, tb, match_id = _create_match(client)

        with client.websocket_connect(f"/ws/chat/{match_id}?token={ta}") as ws:
            ws.receive_json()  # connected
            ws.send_json({"content": "Persisted message"})
            ws.receive_json()  # echo

        # Verify via REST
        res = client.get(f"/messages/{match_id}", headers=_auth(ta))
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["content"] == "Persisted message"

    def test_ws_mark_read_after_receive(self, client: TestClient):
        ta, tb, match_id = _create_match(client)

        # A sends a message
        with client.websocket_connect(f"/ws/chat/{match_id}?token={ta}") as ws:
            ws.receive_json()
            ws.send_json({"content": "Read me!"})
            ws.receive_json()

        # B marks as read
        res = client.put(f"/messages/{match_id}/read", headers=_auth(tb))
        assert res.status_code == 200
        assert res.json()["marked_read"] == 1

        # A marks read (nothing to mark from B's side yet)
        res2 = client.put(f"/messages/{match_id}/read", headers=_auth(ta))
        assert res2.json()["marked_read"] == 0

    def test_ws_empty_message_rejected(self, client: TestClient):
        ta, tb, match_id = _create_match(client)

        with client.websocket_connect(f"/ws/chat/{match_id}?token={ta}") as ws:
            ws.receive_json()  # connected
            ws.send_json({"content": "   "})
            err = ws.receive_json()
            assert err["event"] == "error"
            assert err["code"] == "EMPTY_CONTENT"

    def test_ws_non_member_rejected(self, client: TestClient):
        ta, tb, match_id = _create_match(client)
        tc = _reg_login(client, "chat_ws_outsider@test.com")

        with client.websocket_connect(f"/ws/chat/{match_id}?token={tc}") as ws:
            err = ws.receive_json()
            assert err["event"] == "error"
            # Either NOT_MATCH_MEMBER (match found but user not a member) or
            # MATCH_NOT_FOUND — both correctly reject the outsider
            assert err["code"] in ("NOT_MATCH_MEMBER", "MATCH_NOT_FOUND")

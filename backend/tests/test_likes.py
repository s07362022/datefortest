"""Tests for Like, Pass, Match endpoints and mutual-match logic."""

import pytest
from fastapi.testclient import TestClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _reg_login(client: TestClient, email: str, pw: str = "Like1234!") -> str:
    client.post("/auth/register", json={"email": email, "password": pw})
    res = client.post("/auth/login", json={"email": email, "password": pw})
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _user_id(client: TestClient, token: str) -> int:
    return client.get("/auth/me", headers=_auth(token)).json()["id"]


# ── Like ──────────────────────────────────────────────────────────────────────

class TestLike:
    def test_like_success_no_match(self, client: TestClient):
        ta = _reg_login(client, "like_a@test.com")
        tb = _reg_login(client, "like_b@test.com")
        b_id = _user_id(client, tb)

        res = client.post(f"/likes/{b_id}", headers=_auth(ta))
        assert res.status_code == 200
        data = res.json()
        assert data["is_match"] is False
        assert data["match_id"] is None

    def test_like_mutual_creates_match(self, client: TestClient):
        ta = _reg_login(client, "mutual_a@test.com")
        tb = _reg_login(client, "mutual_b@test.com")
        a_id = _user_id(client, ta)
        b_id = _user_id(client, tb)

        # A likes B
        client.post(f"/likes/{b_id}", headers=_auth(ta))
        # B likes A — should create match
        res = client.post(f"/likes/{a_id}", headers=_auth(tb))
        assert res.status_code == 200
        data = res.json()
        assert data["is_match"] is True
        assert data["match_id"] is not None

    def test_like_self_rejected(self, client: TestClient):
        ta = _reg_login(client, "selflike@test.com")
        a_id = _user_id(client, ta)
        res = client.post(f"/likes/{a_id}", headers=_auth(ta))
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "SELF_LIKE"

    def test_like_duplicate_rejected(self, client: TestClient):
        ta = _reg_login(client, "dup_like_a@test.com")
        tb = _reg_login(client, "dup_like_b@test.com")
        b_id = _user_id(client, tb)
        client.post(f"/likes/{b_id}", headers=_auth(ta))
        res = client.post(f"/likes/{b_id}", headers=_auth(ta))
        assert res.status_code == 409
        assert res.json()["detail"]["code"] == "ALREADY_ACTED"

    def test_like_requires_auth(self, client: TestClient):
        res = client.post("/likes/1")
        assert res.status_code == 401


# ── Pass ──────────────────────────────────────────────────────────────────────

class TestPass:
    def test_pass_success(self, client: TestClient):
        ta = _reg_login(client, "pass_a@test.com")
        tb = _reg_login(client, "pass_b@test.com")
        b_id = _user_id(client, tb)
        res = client.post(f"/passes/{b_id}", headers=_auth(ta))
        assert res.status_code == 200
        assert res.json()["message"] == "已略過"

    def test_pass_idempotent(self, client: TestClient):
        """Passing twice should not raise an error."""
        ta = _reg_login(client, "passdup_a@test.com")
        tb = _reg_login(client, "passdup_b@test.com")
        b_id = _user_id(client, tb)
        client.post(f"/passes/{b_id}", headers=_auth(ta))
        res = client.post(f"/passes/{b_id}", headers=_auth(ta))
        assert res.status_code == 200

    def test_pass_self_rejected(self, client: TestClient):
        ta = _reg_login(client, "selfpass@test.com")
        a_id = _user_id(client, ta)
        res = client.post(f"/passes/{a_id}", headers=_auth(ta))
        assert res.status_code == 400

    def test_pass_requires_auth(self, client: TestClient):
        res = client.post("/passes/1")
        assert res.status_code == 401


# ── Matches ───────────────────────────────────────────────────────────────────

class TestMatches:
    def test_matches_empty(self, client: TestClient):
        ta = _reg_login(client, "match_empty@test.com")
        res = client.get("/matches", headers=_auth(ta))
        assert res.status_code == 200
        assert res.json() == []

    def test_matches_after_mutual_like(self, client: TestClient):
        ta = _reg_login(client, "match_full_a@test.com")
        tb = _reg_login(client, "match_full_b@test.com")
        a_id = _user_id(client, ta)
        b_id = _user_id(client, tb)

        client.post(f"/likes/{b_id}", headers=_auth(ta))
        client.post(f"/likes/{a_id}", headers=_auth(tb))

        res_a = client.get("/matches", headers=_auth(ta))
        res_b = client.get("/matches", headers=_auth(tb))

        assert len(res_a.json()) == 1
        assert len(res_b.json()) == 1
        assert res_a.json()[0]["other_user_id"] == b_id
        assert res_b.json()[0]["other_user_id"] == a_id

    def test_unmatch(self, client: TestClient):
        ta = _reg_login(client, "unmatch_a@test.com")
        tb = _reg_login(client, "unmatch_b@test.com")
        a_id = _user_id(client, ta)
        b_id = _user_id(client, tb)

        client.post(f"/likes/{b_id}", headers=_auth(ta))
        client.post(f"/likes/{a_id}", headers=_auth(tb))

        matches = client.get("/matches", headers=_auth(ta)).json()
        match_id = matches[0]["id"]

        res = client.delete(f"/matches/{match_id}", headers=_auth(ta))
        assert res.status_code == 204

        assert client.get("/matches", headers=_auth(ta)).json() == []
        assert client.get("/matches", headers=_auth(tb)).json() == []

    def test_unmatch_not_found(self, client: TestClient):
        ta = _reg_login(client, "unmatch_nf@test.com")
        res = client.delete("/matches/99999", headers=_auth(ta))
        assert res.status_code == 404

    def test_unmatch_other_user_rejected(self, client: TestClient):
        ta = _reg_login(client, "unmatch_rej_a@test.com")
        tb = _reg_login(client, "unmatch_rej_b@test.com")
        tc = _reg_login(client, "unmatch_rej_c@test.com")
        a_id = _user_id(client, ta)
        b_id = _user_id(client, tb)

        client.post(f"/likes/{b_id}", headers=_auth(ta))
        client.post(f"/likes/{a_id}", headers=_auth(tb))
        match_id = client.get("/matches", headers=_auth(ta)).json()[0]["id"]

        res = client.delete(f"/matches/{match_id}", headers=_auth(tc))
        assert res.status_code == 403

    def test_matches_requires_auth(self, client: TestClient):
        res = client.get("/matches")
        assert res.status_code == 401


# ── Daily Quota ───────────────────────────────────────────────────────────────

class TestLikeQuota:
    def test_quota_returns_correct_structure(self, client: TestClient):
        ta = _reg_login(client, "quota_check@test.com")
        res = client.get("/likes/quota", headers=_auth(ta))
        assert res.status_code == 200
        data = res.json()
        assert "used" in data
        assert "limit" in data
        assert "remaining" in data
        assert "resets_at" in data
        assert data["remaining"] == data["limit"] - data["used"]

    def test_quota_decrements_on_like(self, client: TestClient):
        ta = _reg_login(client, "quota_dec_a@test.com")
        tb = _reg_login(client, "quota_dec_b@test.com")
        b_id = _user_id(client, tb)

        before = client.get("/likes/quota", headers=_auth(ta)).json()["used"]
        client.post(f"/likes/{b_id}", headers=_auth(ta))
        after = client.get("/likes/quota", headers=_auth(ta)).json()["used"]
        assert after == before + 1

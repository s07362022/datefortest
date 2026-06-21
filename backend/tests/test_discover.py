"""Tests for GET /discover endpoint."""

import io
from datetime import date

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.models.photo import ModerationStatusEnum, Photo
from app.models.preference import Preference
from app.models.profile import GenderEnum, InterestedInEnum, Profile
from app.models.tag import ProfileTag, Tag


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_jpeg(width=500, height=500) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(80, 120, 60)).save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


def _register_and_login(client: TestClient, email: str, password: str = "Pass1234!") -> str:
    client.post("/auth/register", json={"email": email, "password": password})
    res = client.post("/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _complete_profile(client: TestClient, token: str, db, email_suffix: str = "") -> None:
    """Fill profile to meet is_profile_complete() requirements."""
    headers = _auth(token)
    # Get user id from /me
    me = client.get("/profiles/me", headers=headers).json()
    user_id = me["user_id"]

    # Update profile fields
    client.put("/profiles/me", headers=headers, json={
        "display_name": f"User{email_suffix}",
        "birthday": "1995-06-15",
        "gender": "woman",
        "interested_in": "everyone",
        "city": "台北",
        "bio": "這是一段超過二十個中文字的個人簡介，希望可以認識志同道合的朋友。",
    })

    # Ensure at least 3 tags exist
    tags = db.query(Tag).limit(3).all()
    if not tags:
        for name in ["旅遊", "音樂", "電影"]:
            t = Tag(name=name)
            db.add(t)
        db.flush()
        tags = db.query(Tag).limit(3).all()

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    for tag in tags:
        existing = db.query(ProfileTag).filter(
            ProfileTag.profile_id == profile.id,
            ProfileTag.tag_id == tag.id,
        ).first()
        if not existing:
            db.add(ProfileTag(profile_id=profile.id, tag_id=tag.id))
    db.flush()

    # Upload a photo
    client.post("/photos", headers=headers, files={"file": ("t.jpg", _make_jpeg(), "image/jpeg")})


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestDiscover:
    def test_discover_requires_auth(self, client: TestClient):
        res = client.get("/discover")
        assert res.status_code == 401

    def test_discover_incomplete_profile_blocked(self, client: TestClient, db):
        token = _register_and_login(client, "disco_incomplete@test.com")
        res = client.get("/discover", headers=_auth(token))
        assert res.status_code == 403
        assert res.json()["detail"]["code"] == "PROFILE_INCOMPLETE"

    def test_discover_returns_other_users(self, client: TestClient, db):
        """With a complete profile, discover should return other users (or empty list)."""
        token = _register_and_login(client, "disco_main@test.com")
        _complete_profile(client, token, db, "Main")

        res = client.get("/discover", headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_discover_self_excluded(self, client: TestClient, db):
        """The calling user should never appear in their own discover list."""
        token = _register_and_login(client, "disco_noself@test.com")
        _complete_profile(client, token, db, "NoSelf")

        me = client.get("/profiles/me", headers=_auth(token)).json()
        me_id = me["user_id"]

        res = client.get("/discover", headers=_auth(token))
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert item["user_id"] != me_id

    def test_discover_pagination_limit(self, client: TestClient, db):
        """Limit parameter is respected."""
        token = _register_and_login(client, "disco_page@test.com")
        _complete_profile(client, token, db, "Page")

        res = client.get("/discover?limit=1", headers=_auth(token))
        assert res.status_code == 200
        assert len(res.json()["items"]) <= 1

    def test_discover_response_shape(self, client: TestClient, db):
        """Verify required fields exist in each discover item."""
        token = _register_and_login(client, "disco_shape@test.com")
        _complete_profile(client, token, db, "Shape")

        res = client.get("/discover", headers=_auth(token))
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert "user_id" in item
            assert "display_name" in item
            assert "tags" in item

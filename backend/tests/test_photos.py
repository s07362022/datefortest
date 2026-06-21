"""Tests for photo upload, listing, deletion, and primary setting endpoints."""

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_jpeg(width=500, height=500) -> bytes:
    """Generate a minimal valid JPEG in memory."""
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(120, 80, 60)).save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


def _register_and_login(client: TestClient, email: str = "photo_user@test.com") -> str:
    client.post("/auth/register", json={"email": email, "password": "Photo1234!"})
    res = client.post("/auth/login", json={"email": email, "password": "Photo1234!"})
    return res.json()["access_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestUploadPhoto:
    def test_upload_success(self, client: TestClient):
        token = _register_and_login(client, "upload_ok@test.com")
        files = {"file": ("test.jpg", _make_jpeg(), "image/jpeg")}
        res = client.post("/photos", headers=_auth_header(token), files=files)
        assert res.status_code == 201
        data = res.json()
        assert data["is_primary"] is True
        assert data["sort_order"] == 0
        assert data["moderation_status"] == "pending"

    def test_upload_requires_auth(self, client: TestClient):
        files = {"file": ("test.jpg", _make_jpeg(), "image/jpeg")}
        res = client.post("/photos", files=files)
        assert res.status_code == 401

    def test_upload_invalid_type(self, client: TestClient):
        token = _register_and_login(client, "upload_type@test.com")
        files = {"file": ("test.txt", b"hello world", "text/plain")}
        res = client.post("/photos", headers=_auth_header(token), files=files)
        assert res.status_code == 422
        assert res.json()["detail"]["code"] == "INVALID_FILE_TYPE"

    def test_upload_too_small(self, client: TestClient):
        token = _register_and_login(client, "upload_small@test.com")
        small_img = _make_jpeg(width=100, height=100)
        files = {"file": ("small.jpg", small_img, "image/jpeg")}
        res = client.post("/photos", headers=_auth_header(token), files=files)
        assert res.status_code == 422
        assert res.json()["detail"]["code"] == "IMAGE_TOO_SMALL"

    def test_upload_second_photo_not_primary(self, client: TestClient):
        token = _register_and_login(client, "upload_two@test.com")
        headers = _auth_header(token)
        for _ in range(2):
            client.post("/photos", headers=headers, files={"file": ("t.jpg", _make_jpeg(), "image/jpeg")})
        res = client.get("/photos/me", headers=headers)
        photos = res.json()
        assert len(photos) == 2
        assert photos[0]["is_primary"] is True
        assert photos[1]["is_primary"] is False

    def test_upload_max_photos_exceeded(self, client: TestClient):
        token = _register_and_login(client, "upload_max@test.com")
        headers = _auth_header(token)
        for _ in range(6):
            r = client.post("/photos", headers=headers, files={"file": ("t.jpg", _make_jpeg(), "image/jpeg")})
            assert r.status_code == 201
        # 7th should fail
        r = client.post("/photos", headers=headers, files={"file": ("t.jpg", _make_jpeg(), "image/jpeg")})
        assert r.status_code == 422
        assert r.json()["detail"]["code"] == "MAX_PHOTOS_REACHED"


class TestListPhotos:
    def test_list_empty(self, client: TestClient):
        token = _register_and_login(client, "list_empty@test.com")
        res = client.get("/photos/me", headers=_auth_header(token))
        assert res.status_code == 200
        assert res.json() == []

    def test_list_after_upload(self, client: TestClient):
        token = _register_and_login(client, "list_after@test.com")
        headers = _auth_header(token)
        client.post("/photos", headers=headers, files={"file": ("t.jpg", _make_jpeg(), "image/jpeg")})
        res = client.get("/photos/me", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 1


class TestDeletePhoto:
    def test_delete_success(self, client: TestClient):
        token = _register_and_login(client, "delete_ok@test.com")
        headers = _auth_header(token)
        upload = client.post("/photos", headers=headers, files={"file": ("t.jpg", _make_jpeg(), "image/jpeg")})
        photo_id = upload.json()["id"]
        res = client.delete(f"/photos/{photo_id}", headers=headers)
        assert res.status_code == 204
        assert client.get("/photos/me", headers=headers).json() == []

    def test_delete_not_found(self, client: TestClient):
        token = _register_and_login(client, "delete_nf@test.com")
        res = client.delete("/photos/99999", headers=_auth_header(token))
        assert res.status_code == 404

    def test_delete_primary_reassigns(self, client: TestClient):
        token = _register_and_login(client, "delete_primary@test.com")
        headers = _auth_header(token)
        for _ in range(2):
            client.post("/photos", headers=headers, files={"file": ("t.jpg", _make_jpeg(), "image/jpeg")})
        photos = client.get("/photos/me", headers=headers).json()
        primary_id = next(p["id"] for p in photos if p["is_primary"])
        client.delete(f"/photos/{primary_id}", headers=headers)
        remaining = client.get("/photos/me", headers=headers).json()
        assert len(remaining) == 1
        assert remaining[0]["is_primary"] is True


class TestSetPrimaryPhoto:
    def test_set_primary(self, client: TestClient):
        token = _register_and_login(client, "setprimary@test.com")
        headers = _auth_header(token)
        for _ in range(2):
            client.post("/photos", headers=headers, files={"file": ("t.jpg", _make_jpeg(), "image/jpeg")})
        photos = client.get("/photos/me", headers=headers).json()
        second_id = next(p["id"] for p in photos if not p["is_primary"])
        res = client.put(f"/photos/{second_id}/primary", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_primary"] is True
        assert res.json()["id"] == second_id

    def test_set_primary_not_found(self, client: TestClient):
        token = _register_and_login(client, "setprimary_nf@test.com")
        res = client.put("/photos/99999/primary", headers=_auth_header(token))
        assert res.status_code == 404

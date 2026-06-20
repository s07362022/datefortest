import pytest


REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
ME_URL = "/auth/me"

VALID_EMAIL = "test@example.com"
VALID_PASSWORD = "SecurePass1"


class TestRegister:
    def test_register_success(self, client):
        res = client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        res = client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        assert res.status_code == 409
        assert res.json()["detail"]["code"] == "EMAIL_EXISTS"

    def test_register_weak_password_too_short(self, client):
        res = client.post(REGISTER_URL, json={"email": "new@example.com", "password": "abc"})
        assert res.status_code == 422

    def test_register_weak_password_no_digit(self, client):
        res = client.post(REGISTER_URL, json={"email": "new@example.com", "password": "NoDigitPass"})
        assert res.status_code == 422

    def test_register_invalid_email(self, client):
        res = client.post(REGISTER_URL, json={"email": "not-an-email", "password": VALID_PASSWORD})
        assert res.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        res = client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        assert res.status_code == 200
        assert "access_token" in res.json()

    def test_login_wrong_password(self, client):
        client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        res = client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": "WrongPass9"})
        assert res.status_code == 401
        assert res.json()["detail"]["code"] == "INVALID_CREDENTIALS"

    def test_login_unknown_email(self, client):
        res = client.post(LOGIN_URL, json={"email": "ghost@example.com", "password": VALID_PASSWORD})
        assert res.status_code == 401


class TestMe:
    def _token(self, client) -> str:
        client.post(REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        res = client.post(LOGIN_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD})
        return res.json()["access_token"]

    def test_me_authenticated(self, client):
        token = self._token(client)
        res = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == VALID_EMAIL
        assert data["is_active"] is True

    def test_me_no_token(self, client):
        res = client.get(ME_URL)
        assert res.status_code == 401

    def test_me_invalid_token(self, client):
        res = client.get(ME_URL, headers={"Authorization": "Bearer invalidtoken"})
        assert res.status_code == 401

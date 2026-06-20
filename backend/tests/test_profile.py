from datetime import date


REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
PROFILE_ME_URL = "/profiles/me"
PREF_ME_URL = "/preferences/me"


def _auth_headers(client, email="user@example.com", password="TestPass1") -> dict:
    client.post(REGISTER_URL, json={"email": email, "password": password})
    res = client.post(LOGIN_URL, json={"email": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestProfileUpdate:
    def test_get_empty_profile(self, client):
        headers = _auth_headers(client)
        res = client.get(PROFILE_ME_URL, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["display_name"] is None
        assert data["is_complete"] is False

    def test_update_profile_basic_fields(self, client):
        headers = _auth_headers(client)
        payload = {
            "display_name": "小明",
            "birthday": "1995-06-15",
            "gender": "man",
            "interested_in": "women",
            "city": "台北",
            "bio": "這是一段超過二十個中文字的自我介紹，用來測試最低長度限制是否正確運作",
        }
        res = client.put(PROFILE_ME_URL, json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["display_name"] == "小明"
        assert data["city"] == "台北"
        assert data["gender"] == "man"

    def test_underage_birthday_rejected(self, client):
        headers = _auth_headers(client)
        res = client.put(PROFILE_ME_URL, json={"birthday": "2015-01-01"}, headers=headers)
        assert res.status_code == 422
        assert res.json()["detail"]["code"] == "AGE_RESTRICTION"

    def test_profile_not_complete_without_tags_and_photo(self, client):
        headers = _auth_headers(client)
        payload = {
            "display_name": "小明",
            "birthday": "1995-06-15",
            "gender": "man",
            "interested_in": "women",
            "city": "台北",
            "bio": "這是一段超過二十個中文字的自我介紹，用來測試最低長度限制是否正確運作",
        }
        client.put(PROFILE_ME_URL, json=payload, headers=headers)
        res = client.get(PROFILE_ME_URL, headers=headers)
        assert res.json()["is_complete"] is False  # no tags, no photo


class TestPreferences:
    def test_get_default_preferences(self, client):
        headers = _auth_headers(client)
        res = client.get(PREF_ME_URL, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["min_age"] == 18
        assert data["max_age"] == 99
        assert data["max_distance_km"] == 50

    def test_update_preferences(self, client):
        headers = _auth_headers(client)
        payload = {"min_age": 25, "max_age": 35, "max_distance_km": 20, "preferred_genders": ["women", "non_binary"]}
        res = client.put(PREF_ME_URL, json=payload, headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["min_age"] == 25
        assert data["max_age"] == 35
        assert "women" in data["preferred_genders"]

    def test_invalid_age_range(self, client):
        headers = _auth_headers(client)
        res = client.put(PREF_ME_URL, json={"min_age": 10}, headers=headers)
        assert res.status_code == 422

    def test_invalid_gender_value(self, client):
        headers = _auth_headers(client)
        res = client.put(PREF_ME_URL, json={"preferred_genders": ["aliens"]}, headers=headers)
        assert res.status_code == 422

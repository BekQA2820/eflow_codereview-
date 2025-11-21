import pytest

PROFILE_PATH = "/api/v1/profile"

@pytest.mark.parametrize("body", [{"about_me": "Новый текст"}])
def test_api_profile_forbidden(api_client, auth_header_other_user, body):
    """
    Проверяет запрет изменения чужого профиля.
    """
    prid = "employee-123"   # чужой PRID, не совпадает с токеном

    r = api_client.patch(f"{PROFILE_PATH}/{prid}/about-me",
                         json=body,
                         headers=auth_header_other_user)

    assert r.status_code == 403
    data = r.json()

    assert data["code"] == "FORBIDDEN"
    assert "traceId" in data

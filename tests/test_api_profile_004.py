
PROFILE_PATH = "/api/v1/profile"

def test_api_profile_missing_about_me(api_client, auth_header):
    """
    PATCH без обязательного поля about_me должен выдать 400 Bad Request
    """
    prid = "employee-123"

    r = api_client.patch(
        f"{PROFILE_PATH}/{prid}/about-me",
        json={},    # пустое тело
        headers=auth_header
    )

    assert r.status_code == 400
    data = r.json()

    assert data["code"] == "VALIDATION_ERROR"
    assert "details" in data
    assert any("about_me" in d["field"] for d in data["details"])

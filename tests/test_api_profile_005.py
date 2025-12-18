
PROFILE_PATH = "/api/v1/profile"

def test_api_profile_xss_filtering(api_client, auth_header):
    """
    Сервис должен фильтровать HTML и JS.
    """
    prid = "employee-123"
    payload = {"about_me": "<script>alert('xss')</script>"}

    r1 = api_client.patch(
        f"{PROFILE_PATH}/{prid}/about-me",
        json=payload,
        headers=auth_header
    )

    assert r1.status_code == 200

    r2 = api_client.get(f"{PROFILE_PATH}/{prid}", headers=auth_header)
    assert r2.status_code == 200

    about_me = r2.json().get("about_me")

    # Нельзя возвращать сырые HTML/JS
    assert "<script>" not in about_me
    assert "alert(" not in about_me

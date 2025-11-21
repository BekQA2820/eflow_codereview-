def test_profile_xss_sanitization(api_client, auth_header, test_prid):
    """
    Проверка HTML-теги должны быть экранированы или очищены.
    """
    payload = {"about_me": "<script>alert(1)</script>"}

    resp = api_client.patch(f"/api/v1/profile/{test_prid}/about-me",
                            json=payload,
                            headers=auth_header)

    assert resp.status_code == 200

    get_r = api_client.get(f"/api/v1/profile/{test_prid}", headers=auth_header)
    assert get_r.status_code == 200

    about = get_r.json().get("about_me")
    assert "<script>" not in about
    assert "alert(1)" not in about

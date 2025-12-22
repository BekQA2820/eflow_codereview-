PROFILE = "/api/v1/profile/{prid}/about-me"


def test_profile_xss_filter(api_client, valid_prid, auth_header):
    payload = {"about_me": "<script>alert(1)</script>"}

    r = api_client.patch(PROFILE.format(prid=valid_prid),
                         headers=auth_header, json=payload)
    assert r.status_code == 200

    # GET профиль
    r2 = api_client.get(f"/api/v1/profile/{valid_prid}", headers=auth_header)
    assert r2.status_code == 200

    about_me = r2.json().get("about_me")

    assert "<script>" not in about_me
    assert "&lt;script&gt;" in about_me or "alert" not in about_me

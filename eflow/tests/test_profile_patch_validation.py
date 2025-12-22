def test_profile_patch_length_validation(api_client, auth_header):
    long_text = "A" * 2000  # превышает

    response = api_client.patch(
        "/api/v1/profile/123/about-me",
        headers=auth_header,
        json={"about_me": long_text}
    )

    assert response.status_code == 400

    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "about_me" in body.get("details", [])

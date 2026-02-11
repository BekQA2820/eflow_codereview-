from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_010_same_profile_different_roles_different_etag(
    mocker,
    api_client,
):
    body_role_a = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
        "email": "john.doe@example.com",
    }

    body_role_b = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    resp_a = make_json_response(
        status=200,
        body=body_role_a,
        headers={
            "ETag": '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
            "X-Cache": "MISS",
            "Vary": "Authorization, X-Roles-Hash",
            "Cache-Control": "private, no-store",
        },
    )

    resp_b = make_json_response(
        status=200,
        body=body_role_b,
        headers={
            "ETag": '"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"',
            "X-Cache": "MISS",
            "Vary": "Authorization, X-Roles-Hash",
            "Cache-Control": "private, no-store",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_a, resp_b]

    r_a = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer role-a"},
    )

    r_b = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer role-b"},
    )

    assert r_a.status_code == 200
    assert r_b.status_code == 200

    assert r_a.headers["ETag"] != r_b.headers["ETag"]
    assert not r_a.headers["ETag"].startswith("W/")
    assert not r_b.headers["ETag"].startswith("W/")

    assert r_a.json() != r_b.json()

    assert "email" in r_a.json()
    assert "email" not in r_b.json()

    assert "Authorization" in r_a.headers["Vary"]
    assert "X-Roles-Hash" in r_a.headers["Vary"]

    assert r_a.headers["X-Cache"] == "MISS"
    assert r_b.headers["X-Cache"] == "MISS"

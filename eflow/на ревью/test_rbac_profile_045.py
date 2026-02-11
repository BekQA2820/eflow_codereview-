from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_045_role_case_normalization(
    mocker,
    api_client,
):
    body = {
        "profile_id": PROFILE_ID,
        "displayName": "Admin User",
        "email": "admin@example.com",
    }

    resp_upper = make_json_response(
        status=200,
        body=body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-admin"',
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    resp_lower = make_json_response(
        status=200,
        body=body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-admin"',
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_upper, resp_lower]

    r1 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer ADMIN"})
    r2 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer admin"})

    assert r1.status_code == 200
    assert r2.status_code == 200

    assert r1.json() == r2.json()
    assert r1.headers.get("X-Roles-Hash") == r2.headers.get("X-Roles-Hash")

from responses import make_json_response

PROFILE_ID_A = "3fa85f64-5717-4562-b3fc-aaaaaaaaaaaa"
PROFILE_ID_B = "3fa85f64-5717-4562-b3fc-bbbbbbbbbbbb"

ENDPOINT_A = f"/api/v1/profile/{PROFILE_ID_A}"
ENDPOINT_B = f"/api/v1/profile/{PROFILE_ID_B}"


def test_rbac_profile_049_user_data_isolation_same_roles(
    mocker,
    api_client,
):
    body_a = {
        "profile_id": PROFILE_ID_A,
        "displayName": "User A",
        "email": "a@example.com",
    }

    body_b = {
        "profile_id": PROFILE_ID_B,
        "displayName": "User B",
        "email": "b@example.com",
    }

    resp_a_first = make_json_response(
        status=200,
        body=body_a,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-a"',
            "X-Roles-Hash": "cccccccccccccccccccccccccccccccc",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Cache": "MISS",
        },
    )

    resp_a_second = make_json_response(
        status=200,
        body=body_a,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-a"',
            "X-Roles-Hash": "cccccccccccccccccccccccccccccccc",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Cache": "HIT",
        },
    )

    resp_b = make_json_response(
        status=200,
        body=body_b,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-b"',
            "X-Roles-Hash": "cccccccccccccccccccccccccccccccc",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Cache": "MISS",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_a_first, resp_a_second, resp_b]

    r_a1 = api_client.get(ENDPOINT_A, headers={"Authorization": "Bearer A"})
    r_a2 = api_client.get(ENDPOINT_A, headers={"Authorization": "Bearer A"})
    r_b = api_client.get(ENDPOINT_B, headers={"Authorization": "Bearer B"})

    assert r_a1.status_code == 200
    assert r_a2.status_code == 200
    assert r_b.status_code == 200

    assert r_a2.headers.get("X-Cache") == "HIT"
    assert r_b.headers.get("X-Cache") == "MISS"

    data_a = r_a1.json()
    data_b = r_b.json()

    assert data_a["profile_id"] != data_b["profile_id"]
    assert data_a["displayName"] != data_b["displayName"]
    assert data_a["email"] != data_b["email"]

    raw_b = r_b.text.lower()
    assert "user a" not in raw_b
    assert "a@example.com" not in raw_b

    for forbidden in [
        "roles",
        "permissions",
        "scopes",
        "internalflags",
        "internalid",
        "stacktrace",
        "exception",
        "<html",
    ]:
        assert forbidden not in r_a1.text.lower()
        assert forbidden not in r_b.text.lower()

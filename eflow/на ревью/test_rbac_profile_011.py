from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_011_cache_isolated_between_roles(
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

    resp_a_first = make_json_response(
        status=200,
        body=body_role_a,
        headers={
            "ETag": '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
            "X-Cache": "MISS",
            "Cache-Control": "private, no-store",
        },
    )

    resp_a_second = make_json_response(
        status=200,
        body=body_role_a,
        headers={
            "ETag": '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
            "X-Cache": "HIT",
            "Cache-Control": "private, no-store",
        },
    )

    resp_b = make_json_response(
        status=200,
        body=body_role_b,
        headers={
            "ETag": '"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"',
            "X-Cache": "MISS",
            "Cache-Control": "private, no-store",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_a_first, resp_a_second, resp_b]

    r_a_1 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer role-a"},
    )

    r_a_2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer role-a"},
    )

    r_b = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer role-b"},
    )

    assert r_a_1.status_code == 200
    assert r_a_2.status_code == 200
    assert r_b.status_code == 200

    assert r_a_2.headers["X-Cache"] == "HIT"
    assert r_b.headers["X-Cache"] == "MISS"

    assert r_a_1.headers["ETag"] != r_b.headers["ETag"]

    assert "public" not in r_a_1.headers["Cache-Control"].lower()
    assert "public" not in r_b.headers["Cache-Control"].lower()

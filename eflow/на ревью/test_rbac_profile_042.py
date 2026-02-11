from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_042_roles_change_forces_cache_miss(
    mocker,
    api_client,
):
    viewer_miss = make_json_response(
        status=200,
        body={"profile_id": PROFILE_ID, "displayName": "User"},
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer"',
            "X-Cache": "MISS",
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    viewer_hit = make_json_response(
        status=200,
        body={"profile_id": PROFILE_ID, "displayName": "User"},
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer"',
            "X-Cache": "HIT",
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    admin_miss = make_json_response(
        status=200,
        body={"profile_id": PROFILE_ID, "displayName": "User", "email": "a@b.com"},
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-admin"',
            "X-Cache": "MISS",
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [viewer_miss, viewer_hit, admin_miss]

    r1 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer viewer"})
    r2 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer viewer"})
    r3 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer admin"})

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r3.status_code == 200

    assert r2.headers.get("X-Cache") == "HIT"
    assert r3.headers.get("X-Cache") == "MISS"

    assert r1.headers.get("ETag") != r3.headers.get("ETag")

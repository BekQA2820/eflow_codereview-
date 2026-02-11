from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_034_cache_isolated_between_roles(
    mocker,
    api_client,
):
    viewer_body = {
        "profile_id": PROFILE_ID,
        "displayName": "User Viewer",
    }

    admin_body = {
        "profile_id": PROFILE_ID,
        "displayName": "User Admin",
        "email": "admin@example.com",
    }

    # viewer first call → MISS
    resp_viewer_miss = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer"',
            "X-Cache": "MISS",
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
            "Cache-Control": "private, max-age=60",
        },
    )

    # viewer second call → HIT
    resp_viewer_hit = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer"',
            "X-Cache": "HIT",
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
            "Cache-Control": "private, max-age=60",
        },
    )

    # admin first call → MISS (must not reuse viewer cache)
    resp_admin_miss = make_json_response(
        status=200,
        body=admin_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-admin"',
            "X-Cache": "MISS",
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
            "Cache-Control": "private, max-age=60",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [
        resp_viewer_miss,
        resp_viewer_hit,
        resp_admin_miss,
    ]

    # viewer first request
    api_client.get(ENDPOINT, headers={"Authorization": "Bearer viewer"})

    # viewer second request
    r_viewer_2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    # admin first request
    r_admin = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer admin"},
    )

    assert r_viewer_2.headers.get("X-Cache") == "HIT"
    assert r_admin.headers.get("X-Cache") == "MISS"
    assert r_viewer_2.headers.get("ETag") != r_admin.headers.get("ETag")

    vary = r_admin.headers.get("Vary", "")
    assert "Authorization" in vary
    assert "X-Roles-Hash" in vary

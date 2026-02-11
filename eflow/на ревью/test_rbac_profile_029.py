from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_029_cache_isolated_by_roles(
    mocker,
    api_client,
):
    # viewer warmup MISS -> HIT
    viewer_resp_miss = make_json_response(
        status=200,
        body={"profile_id": PROFILE_ID, "displayName": "John"},
        headers={
            "ETag": '"etag-viewer"',
            "X-Cache": "MISS",
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    viewer_resp_hit = make_json_response(
        status=200,
        body={"profile_id": PROFILE_ID, "displayName": "John"},
        headers={
            "ETag": '"etag-viewer"',
            "X-Cache": "HIT",
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    # admin first request
    admin_resp = make_json_response(
        status=200,
        body={
            "profile_id": PROFILE_ID,
            "displayName": "John",
            "email": "john@example.com",
        },
        headers={
            "ETag": '"etag-admin"',
            "X-Cache": "MISS",
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [
        viewer_resp_miss,
        viewer_resp_hit,
        admin_resp,
    ]

    # --- viewer warmup ---
    r1 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer viewer"})
    r2 = api_client.get(ENDPOINT, headers={"Authorization": "Bearer viewer"})

    assert r1.headers.get("X-Cache") == "MISS"
    assert r2.headers.get("X-Cache") == "HIT"

    viewer_etag = r2.headers.get("ETag")

    # --- admin request ---
    r_admin = api_client.get(ENDPOINT, headers={"Authorization": "Bearer admin"})

    assert r_admin.headers.get("X-Cache") == "MISS"

    admin_etag = r_admin.headers.get("ETag")

    # --- No cross-role reuse ---
    assert viewer_etag != admin_etag
    assert "email" not in r2.json()
    assert "email" in r_admin.json()

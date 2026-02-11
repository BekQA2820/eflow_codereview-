from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_043_cache_does_not_leak_higher_privileges(
    mocker,
    api_client,
):
    admin_resp = make_json_response(
        status=200,
        body={
            "profile_id": PROFILE_ID,
            "displayName": "User",
            "email": "admin@example.com",
        },
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-admin"',
            "X-Cache": "MISS",
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    viewer_resp = make_json_response(
        status=200,
        body={
            "profile_id": PROFILE_ID,
            "displayName": "User",
        },
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer"',
            "X-Cache": "MISS",
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [admin_resp, viewer_resp]

    r_admin = api_client.get(ENDPOINT, headers={"Authorization": "Bearer admin"})
    r_viewer = api_client.get(ENDPOINT, headers={"Authorization": "Bearer viewer"})

    assert r_admin.status_code == 200
    assert r_viewer.status_code == 200

    data_admin = r_admin.json()
    data_viewer = r_viewer.json()

    assert "email" in data_admin
    assert "email" not in data_viewer

    assert r_admin.headers.get("ETag") != r_viewer.headers.get("ETag")

    raw_viewer = r_viewer.text.lower()
    assert "roles" not in raw_viewer
    assert "permissions" not in raw_viewer
    assert "scopes" not in raw_viewer

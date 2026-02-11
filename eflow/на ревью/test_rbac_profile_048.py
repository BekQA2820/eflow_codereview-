from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_048_different_roles_different_etag(
    mocker,
    api_client,
):
    viewer_body = {
        "profile_id": PROFILE_ID,
        "displayName": "User",
    }

    admin_body = {
        "profile_id": PROFILE_ID,
        "displayName": "User",
        "email": "admin@example.com",
    }

    resp_viewer = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer-123"',
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    resp_admin = make_json_response(
        status=200,
        body=admin_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-admin-456"',
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_viewer, resp_admin]

    r_viewer = api_client.get(ENDPOINT, headers={"Authorization": "Bearer viewer"})
    r_admin = api_client.get(ENDPOINT, headers={"Authorization": "Bearer admin"})

    assert r_viewer.status_code == 200
    assert r_admin.status_code == 200

    etag_viewer = r_viewer.headers.get("ETag")
    etag_admin = r_admin.headers.get("ETag")

    assert etag_viewer
    assert etag_admin
    assert etag_viewer != etag_admin

    assert not etag_viewer.startswith("W/")
    assert not etag_admin.startswith("W/")

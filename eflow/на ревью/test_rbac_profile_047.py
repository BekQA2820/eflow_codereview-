from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_047_roles_affect_only_allowed_fields(
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
            "ETag": '"etag-viewer"',
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    resp_admin = make_json_response(
        status=200,
        body=admin_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-admin"',
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

    data_viewer = r_viewer.json()
    data_admin = r_admin.json()

    assert set(data_viewer.keys()).issubset(set(data_admin.keys()))
    assert "email" not in data_viewer
    assert "email" in data_admin

    assert None not in data_viewer.values()
    assert {} not in data_viewer.values()

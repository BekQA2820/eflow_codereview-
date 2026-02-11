from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_019_different_roles_return_different_representations(
    mocker,
    api_client,
):
    body_admin = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
        "email": "john.doe@example.com",
    }

    body_viewer = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    resp_admin = make_json_response(
        status=200,
        body=body_admin,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "private, no-store",
        },
    )

    resp_viewer = make_json_response(
        status=200,
        body=body_viewer,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "private, no-store",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_admin, resp_viewer]

    r_admin = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer admin"},
    )

    r_viewer = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    assert r_admin.status_code == 200
    assert r_viewer.status_code == 200

    assert set(r_admin.json().keys()) >= set(r_viewer.json().keys())

    assert "email" in r_admin.json()
    assert "email" not in r_viewer.json()

    for forbidden in ["roles", "permissions", "scopes"]:
        assert forbidden not in r_admin.json()
        assert forbidden not in r_viewer.json()

    assert "public" not in r_admin.headers["Cache-Control"].lower()
    assert "public" not in r_viewer.headers["Cache-Control"].lower()

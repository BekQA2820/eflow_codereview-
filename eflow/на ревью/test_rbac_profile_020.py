import re
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_020_etag_differs_between_roles(
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
            "ETag": '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"',
            "Vary": "Authorization, X-Roles-Hash",
            "Content-Type": "application/json",
        },
    )

    resp_viewer = make_json_response(
        status=200,
        body=body_viewer,
        headers={
            "ETag": '"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"',
            "Vary": "Authorization, X-Roles-Hash",
            "Content-Type": "application/json",
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

    etag_admin = r_admin.headers.get("ETag")
    etag_viewer = r_viewer.headers.get("ETag")

    assert etag_admin is not None
    assert etag_viewer is not None
    assert etag_admin != etag_viewer

    assert not etag_admin.startswith("W/")
    assert not etag_viewer.startswith("W/")

    assert re.fullmatch(r'"[0-9a-f]{32}"', etag_admin)
    assert re.fullmatch(r'"[0-9a-f]{32}"', etag_viewer)

    assert "Authorization" in r_admin.headers.get("Vary", "")
    assert "X-Roles-Hash" in r_admin.headers.get("Vary", "")

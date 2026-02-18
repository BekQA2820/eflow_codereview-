from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_036_forbidden_role_does_not_expand_fields(
    mocker,
    api_client,
):
    guest_body = {
        "profile_id": PROFILE_ID,
        "displayName": "User",
    }

    viewer_body = {
        "profile_id": PROFILE_ID,
        "displayName": "User",
    }

    resp_guest = make_json_response(
        status=200,
        body=guest_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-guest"',
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    resp_viewer = make_json_response(
        status=200,
        body=viewer_body,
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-viewer"',
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_guest, resp_viewer]

    r_guest = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer guest"},
    )

    r_viewer = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer viewer"},
    )

    assert r_guest.status_code == 200
    assert r_viewer.status_code == 200

    guest_fields = set(r_guest.json().keys())
    viewer_fields = set(r_viewer.json().keys())

    # guest must not receive more fields than viewer
    assert guest_fields.issubset(viewer_fields)

    raw_guest = r_guest.text.lower()
    deny = ["email", "internalflags", "stacktrace", "<html"]
    for token in deny:
        assert token not in raw_guest

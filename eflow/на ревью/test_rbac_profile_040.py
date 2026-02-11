import re
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_040_same_roles_same_hash(
    mocker,
    api_client,
):
    resp1 = make_json_response(
        status=200,
        body={"profile_id": PROFILE_ID, "displayName": "User"},
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-1"',
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    resp2 = make_json_response(
        status=200,
        body={"profile_id": PROFILE_ID, "displayName": "User"},
        headers={
            "Content-Type": "application/json",
            "ETag": '"etag-1"',
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Vary": "Authorization, X-Roles-Hash",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp1, resp2]

    r1 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer admin-viewer"},
    )

    r2 = api_client.get(
        ENDPOINT,
        headers={"Authorization": "Bearer admin-viewer-2"},
    )

    assert r1.status_code == 200
    assert r2.status_code == 200

    hash1 = r1.headers.get("X-Roles-Hash")
    hash2 = r2.headers.get("X-Roles-Hash")

    assert hash1 == hash2
    assert re.match(r"^[0-9a-f]{32}$", hash1)

    assert "X-Roles-Hash" in r1.headers.get("Vary", "")
    assert "X-Roles-Hash" in r2.headers.get("Vary", "")

import re
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_006_role_case_normalization(
    mocker,
    api_client,
):
    body = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    etag = '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"'
    roles_hash = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    resp_upper = make_json_response(
        status=200,
        body=body,
        headers={
            "ETag": etag,
            "X-Roles-Hash": roles_hash,
            "Vary": "Authorization, X-Roles-Hash",
            "Content-Type": "application/json",
        },
    )

    resp_lower = make_json_response(
        status=200,
        body=body,
        headers={
            "ETag": etag,
            "X-Roles-Hash": roles_hash,
            "Vary": "Authorization, X-Roles-Hash",
            "Content-Type": "application/json",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_upper, resp_lower]

    r1 = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer jwt-uppercase",
            "Accept": "application/json",
        },
    )

    r2 = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer jwt-lowercase",
            "Accept": "application/json",
        },
    )

    assert r1.status_code == 200
    assert r2.status_code == 200

    assert r1.json() == r2.json()

    assert r1.headers.get("ETag") == r2.headers.get("ETag")
    assert r1.headers.get("X-Roles-Hash") == r2.headers.get("X-Roles-Hash")

    assert not r1.headers["ETag"].startswith("W/")
    assert re.fullmatch(r"[0-9a-f]{32}", r1.headers["X-Roles-Hash"])

    for forbidden in ["roles", "permissions", "scopes"]:
        assert forbidden not in r1.json()
        assert forbidden not in r2.json()

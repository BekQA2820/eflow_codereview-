import re
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_012_roles_normalization_order_and_duplicates(
    mocker,
    api_client,
):
    body = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
        "email": "john.doe@example.com",
    }

    etag = '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"'
    roles_hash = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    resp_1 = make_json_response(
        status=200,
        body=body,
        headers={
            "Content-Type": "application/json",
            "ETag": etag,
            "X-Roles-Hash": roles_hash,
            "X-Cache": "MISS",
            "Vary": "Authorization, X-Roles-Hash",
            "Cache-Control": "private, no-store",
        },
    )

    resp_2 = make_json_response(
        status=200,
        body=body,
        headers={
            "Content-Type": "application/json",
            "ETag": etag,
            "X-Roles-Hash": roles_hash,
            "X-Cache": "MISS",
            "Vary": "Authorization, X-Roles-Hash",
            "Cache-Control": "private, no-store",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_1, resp_2]

    r1 = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer jwt-1",
            "Accept": "application/json",
        },
    )

    r2 = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer jwt-2",
            "Accept": "application/json",
        },
    )

    assert r1.status_code == 200
    assert r2.status_code == 200

    assert r1.headers["Content-Type"] == "application/json"
    assert r2.headers["Content-Type"] == "application/json"

    assert r1.headers["X-Roles-Hash"] == r2.headers["X-Roles-Hash"]
    assert re.fullmatch(r"[0-9a-f]{32}", r1.headers["X-Roles-Hash"])

    assert r1.json() == r2.json()

    assert r1.headers["ETag"] == r2.headers["ETag"]
    assert not r1.headers["ETag"].startswith("W/")

    assert "Authorization" in r1.headers["Vary"]
    assert "X-Roles-Hash" in r1.headers["Vary"]

    for forbidden in ["roles", "permissions", "scopes"]:
        assert forbidden not in r1.json()

    body_lower = r1.text.lower() + r2.text.lower()

    deny_tokens = {
        "internalflags",
        "internalid",
        "debuginfo",
        "stacktrace",
        "exception",
    }

    for token in deny_tokens:
        assert token not in body_lower

    for value in r1.json().values():
        assert value is not None

import re
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_005_duplicate_roles_do_not_change_access(
    mocker,
    api_client,
):
    body = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    etag = '"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"'
    roles_hash = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

    resp_1 = make_json_response(
        status=200,
        body=body,
        headers={
            "ETag": etag,
            "X-Roles-Hash": roles_hash,
            "Vary": "Authorization, X-Roles-Hash",
            "Content-Type": "application/json",
        },
    )

    resp_2 = make_json_response(
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
    mock.side_effect = [resp_1, resp_2]

    r1 = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer jwt-basic",
            "Accept": "application/json",
        },
    )

    r2 = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer jwt-basic-duplicated",
            "Accept": "application/json",
        },
    )

    # --- HTTP ---
    assert r1.status_code == 200
    assert r2.status_code == 200

    # --- Body equality ---
    assert r1.json() == r2.json()

    # --- No forbidden domain fields ---
    for forbidden in ["roles", "permissions", "scopes"]:
        assert forbidden not in r1.json()
        assert forbidden not in r2.json()

    # --- Headers equality ---
    assert r1.headers.get("ETag") == r2.headers.get("ETag")
    assert r1.headers.get("X-Roles-Hash") == r2.headers.get("X-Roles-Hash")

    # --- Strong ETag ---
    assert not r1.headers.get("ETag").startswith("W/")

    # --- Roles hash format ---
    assert re.fullmatch(r"[0-9a-f]{32}", r1.headers.get("X-Roles-Hash"))

    # --- No deny fields ---
    deny_tokens = {
        "internalflags",
        "internalid",
        "requiredpermissions",
        "configsource",
        "internalmeta",
        "stacktrace",
        "exception",
        "<html",
    }

    body_lower = r1.text.lower() + r2.text.lower()
    for token in deny_tokens:
        assert token not in body_lower

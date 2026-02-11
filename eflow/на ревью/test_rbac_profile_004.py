import re

PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_004_different_roles_produce_different_etag(
    mocker,
    api_client,
):
    body_basic = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
    }

    body_extended = {
        "profile_id": PROFILE_ID,
        "displayName": "John Doe",
        "email": "john.doe@example.com",
    }

    resp_basic = make_json_response(
        status=200,
        body=body_basic,
        headers={
            "ETag": '"11111111111111111111111111111111"',
            "X-Cache": "MISS",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Roles-Hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "Content-Type": "application/json",
        },
    )

    resp_extended = make_json_response(
        status=200,
        body=body_extended,
        headers={
            "ETag": '"22222222222222222222222222222222"',
            "X-Cache": "MISS",
            "Vary": "Authorization, X-Roles-Hash",
            "X-Roles-Hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "Content-Type": "application/json",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_basic, resp_extended]

    r_basic = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer token-basic",
            "Accept": "application/json",
        },
    )

    r_extended = api_client.get(
        ENDPOINT,
        headers={
            "Authorization": "Bearer token-extended",
            "Accept": "application/json",
        },
    )

    # --- HTTP ---
    assert r_basic.status_code == 200
    assert r_extended.status_code == 200

    # --- ETag ---
    etag_basic = r_basic.headers.get("ETag")
    etag_extended = r_extended.headers.get("ETag")

    assert etag_basic != etag_extended
    assert etag_basic and not etag_basic.startswith("W/")
    assert etag_extended and not etag_extended.startswith("W/")

    # --- Cache isolation ---
    assert "HIT" not in r_extended.headers.get("X-Cache", "")

    # --- Vary ---
    vary = r_basic.headers.get("Vary", "")
    assert "Authorization" in vary
    assert "X-Roles-Hash" in vary

    # --- RBAC difference ---
    assert "email" not in r_basic.json()
    assert "email" in r_extended.json()

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

    body_lower = r_basic.text.lower() + r_extended.text.lower()
    for token in deny_tokens:
        assert token not in body_lower

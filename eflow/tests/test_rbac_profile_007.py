import re
from responses import make_json_response

EXISTING_PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
UNKNOWN_PROFILE_ID = "3fa85f64-5717-4562-b3fc-000000000000"

ENDPOINT_EXISTING = f"/api/v1/profile/{EXISTING_PROFILE_ID}"
ENDPOINT_UNKNOWN = f"/api/v1/profile/{UNKNOWN_PROFILE_ID}"


def test_rbac_profile_007_forbidden_role_no_profile_existence_leak(
    mocker,
    api_client,
):
    error_body = {
        "code": "FORBIDDEN",
        "message": "access denied",
        "details": [],
        "traceId": "trace-123",
    }

    resp_existing = make_json_response(
        status=403,
        body=error_body,
        headers={
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
            "Content-Type": "application/json",
            "X-Request-ID": "trace-123",
        },
    )

    resp_unknown = make_json_response(
        status=403,
        body=error_body,
        headers={
            "Cache-Control": "no-store",
            "Vary": "Authorization, X-Roles-Hash",
            "Content-Type": "application/json",
            "X-Request-ID": "trace-123",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_existing, resp_unknown]

    r_existing = api_client.get(
        ENDPOINT_EXISTING,
        headers={
            "Authorization": "Bearer restricted-token",
            "Accept": "application/json",
        },
    )

    r_unknown = api_client.get(
        ENDPOINT_UNKNOWN,
        headers={
            "Authorization": "Bearer restricted-token",
            "Accept": "application/json",
        },
    )

    # --- Status ---
    assert r_existing.status_code == 403
    assert r_unknown.status_code == 403

    # --- Headers ---
    for r in [r_existing, r_unknown]:
        assert r.headers["Content-Type"] == "application/json"
        assert r.headers["Cache-Control"] == "no-store"
        assert "Authorization" in r.headers["Vary"]
        assert "X-Roles-Hash" in r.headers["Vary"]
        assert "ETag" not in r.headers

    # --- Body structure ---
    assert r_existing.json()["code"] == "FORBIDDEN"
    assert r_unknown.json()["code"] == "FORBIDDEN"

    assert r_existing.json()["message"] == r_unknown.json()["message"]

    # --- No domain fields ---
    forbidden_fields = [
        "profile_uuid",
        "displayname",
        "email",
        "attributes",
        "relationships",
        "layout",
        "widgets",
        "theme",
        "locale",
    ]

    combined_body = r_existing.text.lower() + r_unknown.text.lower()

    for field in forbidden_fields:
        assert field not in combined_body

    # --- Deny-list security ---
    deny_tokens = {
        "internalflags",
        "internalid",
        "stacktrace",
        "exception",
        "debuginfo",
        "internalmeta",
        "<html",
    }

    for token in deny_tokens:
        assert token not in combined_body

import re
from responses import make_json_response

PROFILE_ID = "3fa85f64-5717-4562-b3fc-111111111111"
ENDPOINT = f"/api/v1/profile/{PROFILE_ID}"


def test_rbac_profile_009_missing_authorization_returns_401(
    mocker,
    api_client,
):
    error_body = {
        "code": "UNAUTHORIZED",
        "message": "authentication required",
        "details": [],
        "traceId": "trace-unauthorized",
    }

    resp_1 = make_json_response(
        status=401,
        body=error_body,
        headers={
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "Content-Type": "application/json",
            "X-Request-ID": "trace-unauthorized",
        },
    )

    resp_2 = make_json_response(
        status=401,
        body=error_body,
        headers={
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "Content-Type": "application/json",
            "X-Request-ID": "trace-unauthorized",
        },
    )

    mock = mocker.patch("requests.Session.request")
    mock.side_effect = [resp_1, resp_2]

    r1 = api_client.get(
        ENDPOINT,
        headers={"Accept": "application/json"},
    )

    r2 = api_client.get(
        ENDPOINT,
        headers={"Accept": "application/json"},
    )

    # --- Status ---
    assert r1.status_code == 401
    assert r2.status_code == 401

    # --- Headers ---
    for r in [r1, r2]:
        assert r.headers["Content-Type"] == "application/json"
        assert r.headers["Cache-Control"] == "no-store"
        assert "Authorization" in r.headers["Vary"]
        assert "ETag" not in r.headers
        assert "X-Request-ID" in r.headers

    # --- Body structure ---
    for r in [r1, r2]:
        data = r.json()
        assert data["code"] == "UNAUTHORIZED"
        assert isinstance(data["message"], str)
        assert isinstance(data["details"], list)
        assert isinstance(data["traceId"], str)

    # --- No domain/UI data ---
    combined_body = r1.text.lower() + r2.text.lower()

    forbidden = [
        "profile_uuid",
        "displayname",
        "email",
        "attributes",
        "layout",
        "widgets",
        "theme",
        "locale",
    ]

    for field in forbidden:
        assert field not in combined_body

    # --- Deny-list ---
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

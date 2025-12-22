import json

PROFILE_PATH = "/api/v1/profile/123"
DENY_FIELDS = {
    "internalFlags",
    "backendOnly",
    "serviceRouting",
    "internalMeta",
    "debugInfo",
    "requiredPermissions",
}


def test_error_response_403_forbidden_profile(mocker, api_client):
    error_body = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": "trace-403",
    }

    resp = mocker.Mock()
    resp.status_code = 403
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": "trace-403",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.patch", return_value=resp)

    r = api_client.patch(PROFILE_PATH, headers={"Authorization": "Bearer user-token"})

    assert r.status_code == 403
    assert r.headers["Content-Type"].startswith("application/json")
    assert "public" not in r.headers.get("Cache-Control", "")

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["traceId"] == r.headers["X-Request-ID"]

    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw

    for field in DENY_FIELDS:
        assert field.lower() not in raw

import json

PROFILE_PATH = "/api/v1/profile/non-existing-id"

DENY_FIELDS = {
    "internalFlags",
    "backendOnly",
    "serviceRouting",
    "internalMeta",
    "debugInfo",
    "requiredPermissions",
}


def test_error_response_404_not_found_profile(mocker, api_client):
    error_body = {
        "code": "NOT_FOUND",
        "message": "Profile not found",
        "details": [],
        "traceId": "trace-404-profile",
    }

    resp = mocker.Mock()
    resp.status_code = 404
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": "trace-404-profile",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(PROFILE_PATH, headers={"Authorization": "Bearer valid-token"})

    assert r.status_code == 404
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

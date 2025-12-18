import json

MANIFEST_PATH = "/api/v1/manifest"

DENY_FIELDS = {
    "internalFlags",
    "backendOnly",
    "serviceRouting",
    "internalMeta",
    "debugInfo",
}


def test_error_response_400_validation_error(mocker, api_client):
    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request parameters",
        "details": [
            {
                "field": "limit",
                "message": "must be a number",
                "code": "INVALID_TYPE",
            }
        ],
        "traceId": "trace-400-validation",
    }

    resp = mocker.Mock()
    resp.status_code = 400
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": "trace-400-validation",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(f"{MANIFEST_PATH}?limit=not-a-number")

    assert r.status_code == 400
    assert r.headers["Content-Type"].startswith("application/json")
    assert "public" not in r.headers.get("Cache-Control", "")

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["code"] == "VALIDATION_ERROR"
    assert isinstance(body["details"], list)
    assert body["traceId"] == r.headers["X-Request-ID"]

    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw

    for field in DENY_FIELDS:
        assert field.lower() not in raw

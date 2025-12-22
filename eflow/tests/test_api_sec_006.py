import json
import pytest

DENY_FIELDS = {
    "internalFlags",
    "internalId",
    "serviceRouting",
    "debugInfo",
    "backendOnly",
    "requiredPermissions",
    "internalMeta",
    "configSource",
}


def test_error_response_405_method_not_allowed(mocker, api_client):
    """
    API SEC 006
    Проверка ErrorResponse при неподдерживаемом HTTP-методе
    """

    error_body = {
        "code": "METHOD_NOT_ALLOWED",
        "message": "Method POST is not allowed",
        "details": [],
        "traceId": "trace-405-xyz",
    }

    resp = mocker.Mock()
    resp.status_code = 405
    resp.headers = {
        "Content-Type": "application/json",
        "Allow": "GET",
        "Cache-Control": "no-store",
        "X-Request-ID": "trace-405-xyz",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.post", return_value=resp)

    r = api_client.post("/api/v1/manifest")

    # -----------------------------
    # HTTP
    # -----------------------------
    assert r.status_code == 405
    assert "Allow" in r.headers
    assert "GET" in r.headers["Allow"]

    assert r.headers["Content-Type"].startswith("application/json")

    cache_control = r.headers.get("Cache-Control", "")
    assert "public" not in cache_control

    # -----------------------------
    # Body
    # -----------------------------
    data = r.json()

    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "METHOD_NOT_ALLOWED"
    assert isinstance(data["message"], str)
    assert isinstance(data["details"], list)

    # -----------------------------
    # traceId
    # -----------------------------
    assert data["traceId"] == r.headers["X-Request-ID"]

    # -----------------------------
    # Security hardening
    # -----------------------------
    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw
    assert "exception" not in raw

    for field in DENY_FIELDS:
        assert field not in raw

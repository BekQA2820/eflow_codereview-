import json
import pytest

MANIFEST_PATH = "/api/v1/manifest"

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


def test_invalid_token_signature(mocker, api_client):
    """
    API SEC 008
    JWT с повреждённой / подменённой подписью
    """

    error_body = {
        "code": "INVALID_TOKEN_SIGNATURE",
        "message": "Invalid token signature",
        "details": [],
        "traceId": "trace-invalid-sign",
    }

    resp = mocker.Mock()
    resp.status_code = 401
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": "trace-invalid-sign",
    }
    resp.json.return_value = error_body
    resp.text = json.dumps(error_body)

    mocker.patch("requests.get", return_value=resp)

    headers = {"Authorization": "Bearer corrupted.signature.token"}
    r = api_client.get(MANIFEST_PATH, headers=headers)

    # -----------------------------
    # HTTP
    # -----------------------------
    assert r.status_code == 401
    assert r.headers["Content-Type"].startswith("application/json")

    cache_control = r.headers.get("Cache-Control", "")
    assert "public" not in cache_control

    # -----------------------------
    # Body
    # -----------------------------
    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}

    assert data["code"] == "INVALID_TOKEN_SIGNATURE"
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
    assert "rsa" not in raw
    assert "hs256" not in raw
    assert "algorithm" not in raw

    for field in DENY_FIELDS:
        assert field not in raw

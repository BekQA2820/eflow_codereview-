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


def test_error_response_invalid_token_issuer(mocker, api_client):
    """
    API SEC 007
    JWT с валидной подписью, но неверными iss / aud
    """

    body = {
        "code": "INVALID_TOKEN_ISSUER",
        "message": "Invalid token issuer or audience",
        "details": [],
        "traceId": "trace-invalid-issuer-001",
    }

    response = mocker.Mock()
    response.status_code = 401
    response.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": "trace-invalid-issuer-001",
    }
    response.json.return_value = body
    response.text = json.dumps(body)

    mocker.patch("requests.get", return_value=response)

    fake_token = "jwt-with-wrong-iss-and-aud"

    r = api_client.get(
        MANIFEST_PATH,
        headers={"Authorization": f"Bearer {fake_token}"},
    )

    # -----------------------------
    # HTTP
    # -----------------------------
    assert r.status_code == 401
    assert r.headers["Content-Type"].startswith("application/json")

    cache_control = r.headers.get("Cache-Control", "")
    assert "public" not in cache_control
    assert "max-age" not in cache_control

    # -----------------------------
    # ErrorResponse
    # -----------------------------
    data = r.json()

    for key in ("code", "message", "details", "traceId"):
        assert key in data, f"Отсутствует поле {key}"

    assert data["code"] == "INVALID_TOKEN_ISSUER"
    assert isinstance(data["message"], str)
    assert isinstance(data["details"], list)

    # traceId ↔ X-Request-ID
    assert data["traceId"] == r.headers.get("X-Request-ID")

    # -----------------------------
    # Security
    # -----------------------------
    raw = r.text.lower()
    assert "<html" not in raw
    assert "stacktrace" not in raw
    assert "rsa" not in raw
    assert "algorithm" not in raw

    for forbidden in DENY_FIELDS:
        assert forbidden not in raw

import uuid
import json
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_contract_002_validation_error_schema(mocker, api_client):
    """
    PROFILE CONTRACT 002
    Контракт ErrorResponse для 400 Validation Error
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request",
        "details": [
            {"field": "email", "code": "INVALID_FORMAT"}
        ],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 400
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.post", return_value=resp)

    r = api_client.post("/api/v1/profiles", json={"email": "bad-email"})

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]

    assert isinstance(data["details"], list)
    assert len(data["details"]) == 1
    assert set(data["details"][0].keys()) == {"field", "code"}
    assert data["details"][0]["field"] == "email"
    assert data["details"][0]["code"] == "INVALID_FORMAT"

    for f in DENY_FIELDS:
        assert f not in data
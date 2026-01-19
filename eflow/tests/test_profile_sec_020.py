import uuid
import json
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_sec_020_invalid_access_error_schema(mocker, api_client):
    """
    PROFILE SEC 020
    Контракт ErrorResponse для 403 Invalid Access
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "INVALID_ACCESS",
        "message": "Access is denied for this resource",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 403
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/denied")

    assert r.status_code == 403
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]
    assert data["code"] == "INVALID_ACCESS"
    assert data["details"] == []

    for f in DENY_FIELDS:
        assert f not in data
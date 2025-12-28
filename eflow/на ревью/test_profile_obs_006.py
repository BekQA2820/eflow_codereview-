import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"stackTrace", "exception", "debugInfo", "internalMeta"}


def test_profile_sec_023_invalid_jwt_structure(mocker, api_client):
    """
    PROFILE SEC 023
    Некорректная структура JWT
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "INVALID_TOKEN",
        "message": "Malformed JWT",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 401
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode()

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        "/api/v1/profiles/items/profile-1",
        headers={"Authorization": "Bearer not.a.jwt"},
    )

    assert r.status_code == 401
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["traceId"] == r.headers["X-Request-ID"]
    assert UUID_RE.match(body["traceId"])

    for f in DENY_FIELDS:
        assert f not in body
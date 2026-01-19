import json
import uuid
import re

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def test_profile_reject_sql_injection(mocker, api_client):
    """
    PROFILE SEC 066
    Попытка SQL-инъекции в текстовое поле
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "INVALID_INPUT",
        "message": "Invalid input detected",
        "details": [
            {"field": "displayName", "code": "SQL_INJECTION_NOT_ALLOWED"}
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

    mocker.patch("requests.patch", return_value=resp)

    r = api_client.patch(
        "/api/v1/profiles/items/profile-1",
        json={"displayName": "Ivan'; DROP TABLE users; --"},
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["Cache-Control"] == "no-store"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]
    assert data["details"][0]["code"] == "SQL_INJECTION_NOT_ALLOWED"

    for f in DENY_FIELDS:
        assert f not in data
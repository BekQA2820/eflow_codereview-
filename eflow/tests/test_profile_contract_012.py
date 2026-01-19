import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_contract_012_field_not_allowed(mocker, api_client):
    """
    PROFILE CONTRACT 012
    Передача неразрешённых полей
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "FIELD_NOT_ALLOWED",
        "message": "Field is not allowed",
        "details": [
            {"field": "unexpectedField", "code": "FIELD_NOT_ALLOWED"}
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
        json={"name": "Jane Doe", "unexpectedField": "value"}
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]

    assert data["code"] == "FIELD_NOT_ALLOWED"
    assert data["details"] == [{"field": "unexpectedField", "code": "FIELD_NOT_ALLOWED"}]

    for f in DENY_FIELDS:
        assert f not in data
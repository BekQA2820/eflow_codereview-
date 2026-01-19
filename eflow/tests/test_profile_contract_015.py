import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_contract_015_missing_field(mocker, api_client):
    """
    PROFILE CONTRACT 015
    Ошибка при отсутствии обязательного поля
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "FIELD_MISSING",
        "message": "Required field is missing",
        "details": [
            {"field": "email", "code": "FIELD_MISSING"}
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

    r = api_client.post(
        "/api/v1/profiles/items",
        json={"name": "John Doe", "surname": "Doe"}
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]

    assert data["code"] == "FIELD_MISSING"
    assert data["details"] == [{"field": "email", "code": "FIELD_MISSING"}]

    for f in DENY_FIELDS:
        assert f not in data
import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_contract_006_missing_required_field(mocker, api_client):
    """
    PROFILE CONTRACT 006
    Отсутствие обязательного поля
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "REQUIRED",
        "message": "Required field is missing",
        "details": [
            {"field": "email", "code": "REQUIRED"}
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

    r = api_client.post("/api/v1/profiles/items", json={"name": "Ivan"})

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]

    assert data["code"] == "REQUIRED"
    assert len(data["details"]) == 1
    assert data["details"][0] == {"field": "email", "code": "REQUIRED"}

    for f in DENY_FIELDS:
        assert f not in data
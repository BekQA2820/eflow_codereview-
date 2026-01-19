import uuid
import re
import json

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_neg_002_invalid_field_value(mocker, api_client):
    """
    PROFILE NEG 002
    Некорректное значение поля - строгая валидационная ошибка
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {
                "field": "email",
                "code": "INVALID_FORMAT"
            }
        ],
        "traceId": trace_id
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

    payload = {
        "displayName": "User",
        "email": "not-an-email"
    }

    r = api_client.post("/api/v1/profiles", json=payload)

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert data["traceId"] == r.headers["X-Request-ID"]

    assert data["details"][0]["field"] == "email"
    assert data["details"][0]["code"] == "INVALID_FORMAT"
    assert set(data["details"][0].keys()) == {"field", "code"}

    for f in DENY_FIELDS:
        assert f not in data
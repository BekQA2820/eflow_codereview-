import json
import uuid

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_validation_empty_string_not_allowed(mocker, api_client):
    """
    PROFILE VALID 058
    Пустая строка в поле surname недопустима
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {"field": "surname", "code": "EMPTY_STRING_NOT_ALLOWED"}
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
        "/api/v1/profiles",
        json={
            "name": "Ivan",
            "surname": "",
            "email": "ivan@test.com",
        },
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]
    assert data["details"] == [{"field": "surname", "code": "EMPTY_STRING_NOT_ALLOWED"}]

    for f in DENY_FIELDS:
        assert f not in data
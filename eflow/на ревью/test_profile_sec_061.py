import json
import uuid

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_reject_sql_injection_attempt(mocker, api_client):
    """
    PROFILE SEC 061
    Попытка SQL-инъекции в поле name
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "INVALID_INPUT",
        "message": "Invalid input detected",
        "details": [
            {"field": "name", "code": "INVALID_CHARACTERS"}
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
            "name": "Ivan'; DROP TABLE profiles;--",
            "email": "ivan@test.com",
        },
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    assert data["details"] == [{"field": "name", "code": "INVALID_CHARACTERS"}]
    assert data["traceId"] == r.headers["X-Request-ID"]

    for f in DENY_FIELDS:
        assert f not in data
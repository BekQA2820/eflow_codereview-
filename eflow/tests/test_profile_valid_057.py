import json
import uuid

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_validation_required_field_missing(mocker, api_client):
    """
    PROFILE VALID 057
    Отсутствие обязательного поля name
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {"field": "name", "code": "REQUIRED"}
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
        json={"email": "user@test.com"},
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]
    assert data["details"] == [{"field": "name", "code": "REQUIRED"}]

    for f in DENY_FIELDS:
        assert f not in data
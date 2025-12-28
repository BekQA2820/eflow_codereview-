import json
import uuid
import re


def _assert_uuid(value: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    )


def test_profile_contract_020_error_response_schema(mocker, api_client):
    """
    PROFILE CONTRACT 020
    Строгий ErrorResponse при ошибке валидации
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request",
        "details": [
            {"field": "email", "code": "INVALID_FORMAT"},
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

    r = api_client.post("/api/v1/profiles/items", json={"email": "bad-email"})

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["X-Request-ID"] == trace_id

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "VALIDATION_ERROR"
    assert isinstance(data["details"], list)
    assert data["details"][0] == {"field": "email", "code": "INVALID_FORMAT"}

    _assert_uuid(data["traceId"])

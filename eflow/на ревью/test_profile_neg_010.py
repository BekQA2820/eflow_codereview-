import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_neg_010_missing_required_field(mocker, api_client):
    """
    PROFILE NEG 010
    Отсутствие обязательного поля
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed",
        "details": [
            {"field": "displayName", "code": "REQUIRED"}
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
    resp.content = json.dumps(error_body).encode()

    mocker.patch("requests.post", return_value=resp)

    r = api_client.post("/api/v1/profiles", json={})

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["details"][0] == {"field": "displayName", "code": "REQUIRED"}
    assert body["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(body["traceId"])
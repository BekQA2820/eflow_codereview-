import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_contract_023_error_schema_strict(mocker, api_client):
    """
    PROFILE CONTRACT 023
    Строгий ErrorResponse при неизвестном поле
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "FIELD_NOT_ALLOWED",
        "message": "Unknown field provided",
        "details": [
            {
                "field": "unknown_field",
                "code": "FIELD_NOT_ALLOWED",
            }
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
        "/api/v1/profiles/items/profile-id",
        json={"unknown_field": "value"},
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}

    assert data["code"] == "FIELD_NOT_ALLOWED"
    assert isinstance(data["details"], list)
    assert len(data["details"]) == 1

    d = data["details"][0]
    assert set(d.keys()) == {"field", "code"}
    assert d["code"] == "FIELD_NOT_ALLOWED"

    assert data["traceId"] == r.headers["X-Request-ID"]
    _assert_uuid(data["traceId"])
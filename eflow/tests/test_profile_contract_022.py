import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_contract_022_unknown_field_rejected(mocker, api_client):
    """
    PROFILE CONTRACT 022
    Отклонение неизвестного поля в PATCH
    """

    trace_id = str(uuid.uuid4())

    body = {
        "code": "FIELD_NOT_ALLOWED",
        "message": "Unknown field is not allowed",
        "details": [
            {"field": "unknownField", "code": "FIELD_NOT_ALLOWED"}
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
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.patch", return_value=resp)

    r = api_client.patch(
        "/api/v1/profiles/items/profile-id",
        headers={"If-Match": '"etag-valid"'},
        json={"unknownField": "value"},
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "FIELD_NOT_ALLOWED"
    assert len(data["details"]) == 1
    assert data["details"][0] == {
        "field": "unknownField",
        "code": "FIELD_NOT_ALLOWED",
    }

    _assert_uuid(data["traceId"])
    assert data["traceId"] == r.headers["X-Request-ID"]
import json
import uuid
import re


def _assert_uuid(value: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    )


def test_profile_sec_026_forbidden_field_change(mocker, api_client):
    """
    PROFILE SEC 026
    Запрет изменения защищенного поля профиля
    """

    trace_id = str(uuid.uuid4())

    body = {
        "code": "FIELD_IMMUTABLE",
        "message": "Field cannot be modified",
        "details": [
            {"field": "specialty_sz", "code": "FIELD_IMMUTABLE"}
        ],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 409
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
        json={"specialty_sz": "NEW"},
    )

    assert r.status_code == 409
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "FIELD_IMMUTABLE"
    assert len(data["details"]) == 1
    assert data["details"][0] == {
        "field": "specialty_sz",
        "code": "FIELD_IMMUTABLE",
    }

    _assert_uuid(data["traceId"])
    assert data["traceId"] == r.headers["X-Request-ID"]
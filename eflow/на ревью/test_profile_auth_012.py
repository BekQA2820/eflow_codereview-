import json
import uuid
import re


def _assert_uuid(value: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    ), f"Invalid UUID: {value}"


def test_profile_auth_012_invalid_token(mocker, api_client):
    """
    PROFILE AUTH 012
    Запрос с невалидным Authorization токеном
    """

    trace_id = str(uuid.uuid4())

    body = {
        "code": "UNAUTHORIZED",
        "message": "Invalid token",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 401
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        "/api/v1/profiles/items/profile-id",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert r.status_code == 401
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "UNAUTHORIZED"
    assert data["details"] == []

    _assert_uuid(data["traceId"])
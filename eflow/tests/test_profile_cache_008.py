import json
import uuid
import re


def _assert_uuid(value: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    )


def test_profile_cache_008_no_public_cache_for_error(mocker, api_client):
    """
    PROFILE CACHE 008
    Ошибочные ответы не должны кэшироваться
    """

    trace_id = str(uuid.uuid4())

    body = {
        "code": "NOT_FOUND",
        "message": "Profile not found",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 404
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/unknown-id")

    assert r.status_code == 404
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "NOT_FOUND"
    assert data["details"] == []

    _assert_uuid(data["traceId"])
    assert data["traceId"] == r.headers["X-Request-ID"]
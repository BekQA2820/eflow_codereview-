import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_sec_031_html_not_returned_on_error(mocker, api_client):
    """
    PROFILE SEC 031
    Ошибка никогда не возвращается в HTML
    """

    trace_id = str(uuid.uuid4())

    error_body = {
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
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode()

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/profile-id")

    assert r.status_code == 401
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["traceId"] == r.headers["X-Request-ID"]

    raw = r.content.lower()
    assert b"<html" not in raw
    assert b"<body" not in raw
    assert b"stacktrace" not in raw

    _assert_uuid(body["traceId"])
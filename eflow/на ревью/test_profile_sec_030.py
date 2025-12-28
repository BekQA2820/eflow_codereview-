import json
import uuid
import re


DENY_FIELDS = {"debug", "stackTrace", "exception", "internal"}


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_sec_030_no_internal_fields_on_error(mocker, api_client):
    """
    PROFILE SEC 030
    Ошибочный ответ не содержит внутренних или технических полей
    """

    trace_id = str(uuid.uuid4())

    body = {
        "code": "FORBIDDEN",
        "message": "Access denied",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 403
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/profile-id")

    assert r.status_code == 403
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    for f in DENY_FIELDS:
        assert f not in data

    assert data["traceId"] == r.headers["X-Request-ID"]
    _assert_uuid(data["traceId"])
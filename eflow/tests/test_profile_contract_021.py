import json
import uuid
import re


def _assert_uuid(value: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    )


def test_profile_contract_021_method_not_allowed(mocker, api_client):
    """
    PROFILE CONTRACT 021
    405 Method Not Allowed - строгий контракт ошибки
    """

    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "METHOD_NOT_ALLOWED",
        "message": "Method PUT is not allowed",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 405
    resp.headers = {
        "Content-Type": "application/json",
        "Allow": "GET, POST",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.put", return_value=resp)

    r = api_client.put("/api/v1/profiles/items/profile-1")

    assert r.status_code == 405
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert "GET" in r.headers["Allow"]
    assert r.headers["X-Request-ID"] == trace_id

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "METHOD_NOT_ALLOWED"
    assert data["details"] == []

    _assert_uuid(data["traceId"])
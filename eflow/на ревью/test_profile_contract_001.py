import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def test_profile_response_contract_strict_fields_only(mocker, api_client):
    """
    PROFILE CONTRACT 001
    Строгий контракт ответа профиля без лишних полей
    """

    trace_id = str(uuid.uuid4())

    body = {
        "id": "profile-123",
        "displayName": "Ivan Ivanov",
        "phone": "+79990000000",
        "createdAt": "2024-01-01T10:00:00Z",
        "updatedAt": "2024-01-01T10:00:00Z",
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"v1"',
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/profile-123")

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == '"v1"'
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert set(data.keys()) == {
        "id",
        "displayName",
        "phone",
        "createdAt",
        "updatedAt",
        "traceId",
    }
    assert data["traceId"] == r.headers["X-Request-ID"]

    for f in DENY_FIELDS:
        assert f not in data
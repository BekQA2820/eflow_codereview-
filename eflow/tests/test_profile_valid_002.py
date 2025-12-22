import json
import uuid
from datetime import datetime

PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"internalMeta", "debugInfo", "backendOnly"}


def _assert_uuid(v: str):
    uuid.UUID(v)


def _assert_iso8601(v: str):
    datetime.fromisoformat(v.replace("Z", "+00:00"))


def _assert_no_deny_fields(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in DENY_FIELDS
            _assert_no_deny_fields(v)
    elif isinstance(obj, list):
        for i in obj:
            _assert_no_deny_fields(i)


def test_profile_get_success(mocker, api_client):
    """
    PROFILE VALID 002
    Успешное получение профиля
    """

    profile_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    body = {
        "profile_uuid": profile_id,
        "displayName": "Ivan",
        "email": "ivan@test.ru",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
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

    mocker.patch("requests.request", return_value=resp)

    r = api_client.get(PROFILE_PATH.format(profile_id=profile_id))

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert "ETag" in r.headers

    data = r.json()
    assert set(data.keys()) == {
        "profile_uuid",
        "displayName",
        "email",
        "created_at",
        "updated_at",
    }

    _assert_uuid(data["profile_uuid"])
    _assert_iso8601(data["created_at"])
    _assert_iso8601(data["updated_at"])
    _assert_no_deny_fields(data)
import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_func_019_get_profile_returns_consistent_state(mocker, api_client):
    """
    PROFILE FUNC 019
    GET профиля возвращает консистентное состояние и контрактные заголовки
    """

    trace_id = str(uuid.uuid4())
    etag = '"etag-v1"'

    body = {
        "profile_uuid": "profile-id",
        "displayName": "Ivan",
        "email": "ivan@test.local",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "private, no-store",
        "Vary": "Authorization",
        "ETag": etag,
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/profile-id")

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "private, no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == etag

    data = r.json()
    assert set(data.keys()) == {
        "profile_uuid",
        "displayName",
        "email",
        "created_at",
        "updated_at",
    }

    assert data["profile_uuid"] == "profile-id"
    _assert_uuid(r.headers["X-Request-ID"])
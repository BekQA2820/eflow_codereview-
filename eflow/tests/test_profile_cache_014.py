import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_cache_014_get_profile_cache_headers_strict(mocker, api_client):
    """
    PROFILE CACHE 014
    Проверка строгих cache-заголовков и ETag при GET профиля
    """

    trace_id = str(uuid.uuid4())
    etag = '"profile-etag-v1"'

    body = {
        "profile_uuid": "profile-id",
        "displayName": "Ivan",
        "email": "ivan@test.com",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "private, max-age=60",
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
    assert r.headers["Cache-Control"] == "private, max-age=60"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == etag

    body_resp = r.json()
    assert body_resp["profile_uuid"] == "profile-id"

    _assert_uuid(r.headers["X-Request-ID"])
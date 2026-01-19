import uuid
import re
import json

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def test_profile_cache_003_get_profile_cache_headers(mocker, api_client):
    """
    PROFILE CACHE 003
    Проверка Cache-Control и Vary для GET профиля
    """

    trace_id = str(uuid.uuid4())

    body = {
        "profile_uuid": "11111111-2222-3333-4444-555555555555",
        "displayName": "Ivan",
        "email": "ivan@test.ru"
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"etag-v1"',
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/11111111-2222-3333-4444-555555555555")

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == '"etag-v1"'
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert data == body
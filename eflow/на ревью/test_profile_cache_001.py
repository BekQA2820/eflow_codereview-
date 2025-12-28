import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def test_profile_cache_headers_authorized_request(mocker, api_client):
    """
    PROFILE CACHE 001
    Корректные cache-заголовки для авторизованного GET профиля
    """

    trace_id = str(uuid.uuid4())

    body = {
        "id": "profile-300",
        "displayName": "Cache User",
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"cache-v1"',
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/profile-300")

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == '"cache-v1"'
    assert UUID_RE.match(r.headers["X-Request-ID"])

    data = r.json()
    assert data["traceId"] == r.headers["X-Request-ID"]
import json
import uuid


def test_profile_cache_headers_on_get(mocker, api_client):
    """
    PROFILE CACHE 059
    Проверка Cache-Control, Vary и ETag при GET профиля
    """

    profile_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    etag = "etag-profile-059"

    body = {
        "profile_uuid": profile_id,
        "name": "Ivan",
        "surname": "Ivanov",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": etag,
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(f"/api/v1/profiles/items/{profile_id}")

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == etag
    assert r.headers["X-Request-ID"] == trace_id

    data = r.json()
    assert data["profile_uuid"] == profile_id
    assert data["name"] == "Ivan"
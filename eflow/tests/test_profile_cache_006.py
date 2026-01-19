import json
import uuid
import re


def _assert_uuid(value: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        value,
    )


def test_profile_cache_006_get_no_store_for_authorized(mocker, api_client):
    """
    PROFILE CACHE 006
    Авторизованный GET профиля не должен кэшироваться
    """

    trace_id = str(uuid.uuid4())

    body = {
        "profile_uuid": "profile-id",
        "displayName": "Ivan",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"etag-123"',
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/profile-id")

    assert r.status_code == 200
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["ETag"] == '"etag-123"'

    _assert_uuid(r.headers["X-Request-ID"])

    data = r.json()
    assert data["profile_uuid"] == "profile-id"
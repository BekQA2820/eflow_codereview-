import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_cache_010_authorized_get_not_shared(mocker, api_client):
    """
    PROFILE CACHE 010
    Авторизованный GET не должен быть общим между пользователями
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
        "Cache-Control": "private, no-store",
        "Vary": "Authorization",
        "ETag": '"etag-user"',
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        "/api/v1/profiles/items/profile-id",
        headers={"Authorization": "Bearer user-token"},
    )

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "private, no-store"
    assert r.headers["Vary"] == "Authorization"
    assert "ETag" in r.headers

    data = r.json()
    assert data["profile_uuid"] == "profile-id"

    _assert_uuid(r.headers["X-Request-ID"])
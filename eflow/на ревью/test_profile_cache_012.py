import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_cache_012_private_no_store_for_authorized_get(mocker, api_client):
    """
    PROFILE CACHE 012
    Авторизованный GET не кэшируется публично
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
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = body
    resp.content = json.dumps(body).encode()

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get("/api/v1/profiles/items/profile-id")

    assert r.status_code == 200
    assert r.headers["Cache-Control"] == "private, no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert data["profile_uuid"] == "profile-id"

    _assert_uuid(r.headers["X-Request-ID"])
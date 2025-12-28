import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_func_021_get_reflects_latest_patch(mocker, api_client):
    """
    PROFILE FUNC 021
    GET возвращает актуальное состояние после PATCH
    """

    trace_get_1 = str(uuid.uuid4())
    trace_patch = str(uuid.uuid4())
    trace_get_2 = str(uuid.uuid4())

    etag_v1 = '"etag-1"'
    etag_v2 = '"etag-2"'

    body_initial = {
        "profile_uuid": "profile-id",
        "displayName": "Ivan",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
    }

    body_updated = {
        **body_initial,
        "displayName": "Ivan Updated",
        "updated_at": "2025-01-01T11:00:00Z",
    }

    r_get_1 = mocker.Mock()
    r_get_1.status_code = 200
    r_get_1.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "private, no-store",
        "Vary": "Authorization",
        "ETag": etag_v1,
        "X-Request-ID": trace_get_1,
    }
    r_get_1.json.return_value = body_initial
    r_get_1.content = json.dumps(body_initial).encode()

    r_patch = mocker.Mock()
    r_patch.status_code = 200
    r_patch.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": etag_v2,
        "X-Request-ID": trace_patch,
    }
    r_patch.json.return_value = body_updated
    r_patch.content = json.dumps(body_updated).encode()

    r_get_2 = mocker.Mock()
    r_get_2.status_code = 200
    r_get_2.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "private, no-store",
        "Vary": "Authorization",
        "ETag": etag_v2,
        "X-Request-ID": trace_get_2,
    }
    r_get_2.json.return_value = body_updated
    r_get_2.content = json.dumps(body_updated).encode()

    mocker.patch("requests.get", side_effect=[r_get_1, r_get_2])
    mocker.patch("requests.patch", return_value=r_patch)

    r1 = api_client.get("/api/v1/profiles/items/profile-id")
    r2 = api_client.patch(
        "/api/v1/profiles/items/profile-id",
        headers={"If-Match": etag_v1},
        json={"displayName": "Ivan Updated"},
    )
    r3 = api_client.get("/api/v1/profiles/items/profile-id")

    assert r3.json()["displayName"] == "Ivan Updated"
    assert r3.headers["ETag"] == etag_v2

    _assert_uuid(r3.headers["X-Request-ID"])
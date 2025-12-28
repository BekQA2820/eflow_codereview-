import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_func_020_patch_updates_allowed_fields_only(mocker, api_client):
    """
    PROFILE FUNC 020
    PATCH изменяет только разрешённые поля и сохраняет системные
    """

    trace_get = str(uuid.uuid4())
    trace_patch = str(uuid.uuid4())

    etag_v1 = '"etag-v1"'
    etag_v2 = '"etag-v2"'

    body_get = {
        "profile_uuid": "profile-id",
        "displayName": "Ivan",
        "email": "ivan@test.local",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
    }

    body_patch = {
        **body_get,
        "displayName": "Ivan Updated",
        "updated_at": "2025-01-01T11:00:00Z",
    }

    r_get = mocker.Mock()
    r_get.status_code = 200
    r_get.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "private, no-store",
        "Vary": "Authorization",
        "ETag": etag_v1,
        "X-Request-ID": trace_get,
    }
    r_get.json.return_value = body_get
    r_get.content = json.dumps(body_get).encode()

    r_patch = mocker.Mock()
    r_patch.status_code = 200
    r_patch.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": etag_v2,
        "X-Request-ID": trace_patch,
    }
    r_patch.json.return_value = body_patch
    r_patch.content = json.dumps(body_patch).encode()

    mocker.patch("requests.get", return_value=r_get)
    mocker.patch("requests.patch", return_value=r_patch)

    r1 = api_client.get("/api/v1/profiles/items/profile-id")
    r2 = api_client.patch(
        "/api/v1/profiles/items/profile-id",
        headers={"If-Match": etag_v1},
        json={"displayName": "Ivan Updated"},
    )

    assert r2.status_code == 200
    assert r2.headers["ETag"] == etag_v2

    data = r2.json()
    assert data["displayName"] == "Ivan Updated"
    assert data["email"] == body_get["email"]
    assert data["created_at"] == body_get["created_at"]
    assert data["updated_at"] != body_get["updated_at"]

    _assert_uuid(r2.headers["X-Request-ID"])
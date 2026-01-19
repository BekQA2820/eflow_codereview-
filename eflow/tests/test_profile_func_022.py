import json
import uuid
import re


def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )


def test_profile_func_022_patch_does_not_mutate_unsent_fields(mocker, api_client):
    """
    PROFILE FUNC 022
    PATCH изменяет только переданные поля и не мутирует остальные
    """

    trace_get = str(uuid.uuid4())
    trace_patch = str(uuid.uuid4())

    etag_v1 = '"etag-1"'
    etag_v2 = '"etag-2"'

    body_before = {
        "profile_uuid": "profile-id",
        "displayName": "Ivan",
        "email": "ivan@test.com",
        "phone": "+79990000000",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
    }

    body_after = {
        **body_before,
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
    r_get.json.return_value = body_before
    r_get.content = json.dumps(body_before).encode()

    r_patch = mocker.Mock()
    r_patch.status_code = 200
    r_patch.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": etag_v2,
        "X-Request-ID": trace_patch,
    }
    r_patch.json.return_value = body_after
    r_patch.content = json.dumps(body_after).encode()

    mocker.patch("requests.get", return_value=r_get)
    mocker.patch("requests.patch", return_value=r_patch)

    api_client.get("/api/v1/profiles/items/profile-id")

    r = api_client.patch(
        "/api/v1/profiles/items/profile-id",
        headers={"If-Match": etag_v1},
        json={"displayName": "Ivan Updated"},
    )

    body = r.json()

    assert body["displayName"] == "Ivan Updated"
    assert body["email"] == body_before["email"]
    assert body["phone"] == body_before["phone"]
    assert body["created_at"] == body_before["created_at"]
    assert body["updated_at"] != body_before["updated_at"]

    _assert_uuid(r.headers["X-Request-ID"])
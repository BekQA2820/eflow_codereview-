import json
import uuid
from datetime import datetime

PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"


def _assert_uuid(value: str):
    uuid.UUID(value)


def _assert_iso8601(value: str):
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_profile_update_allowed_fields_only(mocker, api_client):
    """
    PROFILE FUNC 006
    Обновление разрешённых атрибутов профиля
    """

    profile_id = str(uuid.uuid4())
    etag_v1 = "etag-1"
    etag_v2 = "etag-2"

    original = {
        "id": profile_id,
        "name": "Ivan",
        "surname": "Petrov",
        "phone": "+79990000001",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
        "last_modified_by": "system",
    }

    updated = {
        **original,
        "name": "Petr",
        "surname": "Ivanov",
        "updated_at": "2025-01-01T10:10:00Z",
        "last_modified_by": "user-a",
    }

    def make_response(body, etag):
        resp = mocker.Mock()
        resp.status_code = 200
        resp.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "ETag": etag,
            "X-Request-ID": str(uuid.uuid4()),
        }
        resp.json.return_value = body
        resp.content = json.dumps(body).encode("utf-8")
        return resp

    r_get = make_response(original, etag_v1)
    r_patch = make_response(updated, etag_v2)
    r_get_after = make_response(updated, etag_v2)

    mocker.patch("requests.request", side_effect=[r_get, r_patch, r_get_after])

    r1 = api_client.get(PROFILE_PATH.format(profile_id=profile_id))
    assert r1.headers["ETag"] == etag_v1

    r2 = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        headers={"If-Match": etag_v1},
        json={"name": "Petr", "surname": "Ivanov"},
    )

    assert r2.status_code == 200
    assert r2.headers["ETag"] == etag_v2

    body_patch = r2.json()
    assert body_patch["phone"] == original["phone"]
    assert body_patch["created_at"] == original["created_at"]
    assert body_patch["updated_at"] != original["updated_at"]

    r3 = api_client.get(PROFILE_PATH.format(profile_id=profile_id))
    body_get = r3.json()

    assert body_get == body_patch
    _assert_iso8601(body_get["updated_at"])
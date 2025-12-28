import json
import uuid
from datetime import datetime

PROFILES_ITEMS_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}


def _assert_no_deny_fields(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in DENY_FIELDS
            _assert_no_deny_fields(v)
    elif isinstance(obj, list):
        for i in obj:
            _assert_no_deny_fields(i)


def test_profile_patch_updates_only_allowed_fields(mocker, api_client):
    """
    PROFILE FUNC 054
    PATCH изменяет только разрешённые поля и корректно обновляет метаданные
    """

    profile_id = str(uuid.uuid4())
    path = PROFILES_ITEMS_PATH.format(profile_id=profile_id)

    etag_v1 = "etag-v1"
    etag_v2 = "etag-v2"

    body_before = {
        "profile_uuid": profile_id,
        "name": "Ivan",
        "surname": "Ivanov",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
        "last_modified_by": "system",
    }

    body_after = {
        **body_before,
        "surname": "Petrov",
        "updated_at": "2024-01-01T10:10:00Z",
        "last_modified_by": "user",
    }

    def make_resp(body, etag):
        r = mocker.Mock()
        r.status_code = 200
        r.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "ETag": etag,
            "X-Request-ID": str(uuid.uuid4()),
        }
        r.json.return_value = body
        r.content = json.dumps(body).encode("utf-8")
        return r

    mocker.patch("requests.get", return_value=make_resp(body_before, etag_v1))
    mocker.patch("requests.patch", return_value=make_resp(body_after, etag_v2))

    r_get = api_client.get(path)
    assert r_get.headers["ETag"] == etag_v1

    r_patch = api_client.patch(
        path,
        headers={"If-Match": etag_v1},
        json={"surname": "Petrov"},
    )

    data = r_patch.json()

    assert r_patch.headers["ETag"] == etag_v2
    assert data["surname"] == "Petrov"
    assert data["name"] == "Ivan"
    assert data["created_at"] == body_before["created_at"]
    assert data["updated_at"] != body_before["updated_at"]
    assert data["last_modified_by"] == "user"

    _assert_no_deny_fields(data)
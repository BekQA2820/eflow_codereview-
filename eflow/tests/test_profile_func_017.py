import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_func_017_partial_update_does_not_touch_other_fields(mocker, api_client):
    """
    PROFILE FUNC 017
    PATCH изменяет только указанные поля и не мутирует остальные
    """

    profile_id = "profile-123"
    etag_v1 = '"etag-v1"'
    etag_v2 = '"etag-v2"'
    trace_get = str(uuid.uuid4())
    trace_patch = str(uuid.uuid4())

    original = {
        "profile_id": profile_id,
        "name": "Ivan",
        "surname": "Petrov",
        "phone": "+700000000",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
    }

    updated = {
        **original,
        "phone": "+799999999",
        "updated_at": "2024-01-01T11:00:00Z",
    }

    r_get = mocker.Mock()
    r_get.status_code = 200
    r_get.headers = {
        "Content-Type": "application/json",
        "ETag": etag_v1,
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_get,
    }
    r_get.json.return_value = original
    r_get.content = json.dumps(original).encode()

    r_patch = mocker.Mock()
    r_patch.status_code = 200
    r_patch.headers = {
        "Content-Type": "application/json",
        "ETag": etag_v2,
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_patch,
    }
    r_patch.json.return_value = updated
    r_patch.content = json.dumps(updated).encode()

    mocker.patch("requests.get", return_value=r_get)
    mocker.patch("requests.patch", return_value=r_patch)

    g = api_client.get(f"/api/v1/profiles/items/{profile_id}")
    p = api_client.patch(
        f"/api/v1/profiles/items/{profile_id}",
        json={"phone": "+799999999"},
        headers={"If-Match": etag_v1},
    )

    assert g.headers["ETag"] == etag_v1
    assert p.headers["ETag"] == etag_v2

    body = p.json()
    assert body["phone"] == "+799999999"
    assert body["name"] == "Ivan"
    assert body["surname"] == "Petrov"
    assert body["created_at"] == original["created_at"]
    assert body["updated_at"] != original["updated_at"]

    for f in DENY_FIELDS:
        assert f not in body
import json
import uuid
import re

DENY_FIELDS = {"debugInfo", "stackTrace", "internalMeta"}
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")


def test_profile_partial_update_preserves_other_fields(mocker, api_client):
    """
    PROFILE FUNC 064
    PATCH изменяет только указанные поля профиля
    """

    trace_id = str(uuid.uuid4())
    etag_v1 = '"etag-1"'
    etag_v2 = '"etag-2"'

    body_before = {
        "id": "profile-1",
        "email": "user@test.com",
        "phone": "+123",
        "displayName": "Ivan",
    }

    body_after = {
        "id": "profile-1",
        "email": "user@test.com",
        "phone": "+123",
        "displayName": "Ivan Updated",
    }

    r_get = mocker.Mock()
    r_get.status_code = 200
    r_get.headers = {
        "Content-Type": "application/json",
        "ETag": etag_v1,
        "X-Request-ID": trace_id,
    }
    r_get.json.return_value = body_before

    r_patch = mocker.Mock()
    r_patch.status_code = 200
    r_patch.headers = {
        "Content-Type": "application/json",
        "ETag": etag_v2,
        "X-Request-ID": trace_id,
    }
    r_patch.json.return_value = body_after

    mocker.patch("requests.get", return_value=r_get)
    mocker.patch("requests.patch", return_value=r_patch)

    get_resp = api_client.get("/api/v1/profiles/items/profile-1")
    assert get_resp.headers["ETag"] == etag_v1

    patch_resp = api_client.patch(
        "/api/v1/profiles/items/profile-1",
        headers={"If-Match": etag_v1},
        json={"displayName": "Ivan Updated"},
    )

    data = patch_resp.json()

    assert data["displayName"] == "Ivan Updated"
    assert data["email"] == body_before["email"]
    assert data["phone"] == body_before["phone"]
    assert patch_resp.headers["ETag"] == etag_v2
    assert UUID_RE.match(patch_resp.headers["X-Request-ID"])

    for f in DENY_FIELDS:
        assert f not in data
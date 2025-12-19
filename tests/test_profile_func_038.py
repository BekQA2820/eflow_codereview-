import json
import uuid
from datetime import datetime

PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"internalMeta", "debugInfo", "backendOnly"}


def _assert_uuid(value: str):
    uuid.UUID(value)


def _assert_iso8601(value: str):
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def _assert_no_deny_fields(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in DENY_FIELDS
            _assert_no_deny_fields(v)
    elif isinstance(obj, list):
        for i in obj:
            _assert_no_deny_fields(i)


def test_profile_patch_valid_subset_fields(mocker, api_client):
    """
    PROFILE FUNC 038
    PATCH обновляет только переданные поля,
    остальные атрибуты остаются неизменными
    """

    base_profile = {
        "id": str(uuid.uuid4()),
        "displayName": "Ivan Petrov",
        "department": "Sales",
        "phone": "+79990000001",
        "created_at": "2025-01-01T09:00:00Z",
        "updated_at": "2025-01-01T09:00:00Z",
        "last_modified_by": "system",
    }

    updated_profile = {
        **base_profile,
        "displayName": "Ivan P.",
        "updated_at": "2025-01-01T09:10:00Z",
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

    r_get_before = make_response(base_profile, "etag-v1")
    r_patch = make_response(updated_profile, "etag-v2")
    r_get_after = make_response(updated_profile, "etag-v2")

    mocker.patch(
        "requests.request",
        side_effect=[r_get_before, r_patch, r_get_after],
    )

    profile_id = base_profile["id"]

    # -------------------------
    # GET before PATCH
    # -------------------------
    g1 = api_client.get(PROFILE_PATH.format(profile_id=profile_id))
    assert g1.headers["ETag"] == "etag-v1"

    # -------------------------
    # PATCH subset (displayName only)
    # -------------------------
    p = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        headers={"If-Match": "etag-v1"},
        json={"displayName": "Ivan P."},
    )

    assert p.status_code == 200
    assert p.headers["ETag"] == "etag-v2"

    body_patch = p.json()
    _assert_no_deny_fields(body_patch)

    assert body_patch["displayName"] == "Ivan P."
    assert body_patch["department"] == base_profile["department"]
    assert body_patch["phone"] == base_profile["phone"]
    assert body_patch["created_at"] == base_profile["created_at"]
    assert body_patch["updated_at"] != base_profile["updated_at"]

    _assert_iso8601(body_patch["updated_at"])

    # -------------------------
    # GET after PATCH
    # -------------------------
    g2 = api_client.get(PROFILE_PATH.format(profile_id=profile_id))
    body_get = g2.json()

    assert body_get == body_patch

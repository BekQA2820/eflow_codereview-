import json
import uuid
from datetime import datetime

PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"internalMeta", "debugInfo", "backendOnly"}


def _assert_iso8601(v: str):
    datetime.fromisoformat(v.replace("Z", "+00:00"))


def _assert_no_deny_fields(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in DENY_FIELDS
            _assert_no_deny_fields(v)
    elif isinstance(obj, list):
        for i in obj:
            _assert_no_deny_fields(i)


def test_profile_atomic_patch_multiple_fields(mocker, api_client):
    """
    PROFILE FUNC 050
    PATCH с несколькими полями должен применяться атомарно
    """

    profile_id = str(uuid.uuid4())
    etag_v1 = "etag-1"
    etag_v2 = "etag-2"

    base = {
        "id": profile_id,
        "displayName": "Ivan Petrov",
        "department": "Sales",
        "phone": "+79990000001",
        "created_at": "2025-01-01T07:00:00Z",
        "updated_at": "2025-01-01T07:00:00Z",
        "last_modified_by": "system",
    }

    updated = {
        **base,
        "displayName": "Ivan P.",
        "department": "Marketing",
        "updated_at": "2025-01-01T07:10:00Z",
        "last_modified_by": "user-a",
    }

    def resp(body, etag):
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

    mocker.patch(
        "requests.request",
        side_effect=[
            resp(base, etag_v1),     # GET
            resp(updated, etag_v2),  # PATCH
            resp(updated, etag_v2),  # GET after
        ],
    )

    # GET before
    r1 = api_client.get(PROFILE_PATH.format(profile_id=profile_id))
    assert r1.headers["ETag"] == etag_v1

    # PATCH multiple fields
    r2 = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        headers={"If-Match": etag_v1},
        json={
            "displayName": "Ivan P.",
            "department": "Marketing",
        },
    )

    assert r2.status_code == 200
    assert r2.headers["ETag"] == etag_v2

    body_patch = r2.json()
    _assert_no_deny_fields(body_patch)

    assert body_patch["displayName"] == "Ivan P."
    assert body_patch["department"] == "Marketing"
    assert body_patch["phone"] == base["phone"]
    assert body_patch["created_at"] == base["created_at"]
    assert body_patch["updated_at"] != base["updated_at"]
    _assert_iso8601(body_patch["updated_at"])

    # GET after
    r3 = api_client.get(PROFILE_PATH.format(profile_id=profile_id))
    assert r3.json() == body_patch
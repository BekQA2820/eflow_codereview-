import json
import uuid

PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"internalMeta", "debugInfo", "backendOnly"}


def _assert_uuid(v):
    uuid.UUID(v)


def _assert_no_deny_fields(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in DENY_FIELDS
            _assert_no_deny_fields(v)
    elif isinstance(obj, list):
        for i in obj:
            _assert_no_deny_fields(i)


def test_profile_unicode_serialization(mocker, api_client):
    profile_id = str(uuid.uuid4())
    etag_v1 = '"v1"'
    etag_v2 = '"v2"'

    body_get = {
        "profile_uuid": profile_id,
        "displayName": "Иван",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
    }

    body_patch = {
        "profile_uuid": profile_id,
        "displayName": "Иван Петров",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-02T10:00:00Z",
    }

    def make_resp(body, etag):
        trace_id = str(uuid.uuid4())
        r = mocker.Mock()
        r.status_code = 200
        r.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "ETag": etag,
            "X-Request-ID": trace_id,
        }
        r.json.return_value = body
        r.content = json.dumps(body, ensure_ascii=False).encode("utf-8")
        return r

    mocker.patch(
        "requests.request",
        side_effect=[make_resp(body_get, etag_v1), make_resp(body_patch, etag_v2)],
    )

    g = api_client.get(PROFILE_PATH.format(profile_id=profile_id))
    assert g.headers["ETag"] == etag_v1

    p = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        json={"displayName": "Иван Петров"},
        headers={"If-Match": etag_v1},
    )

    assert p.headers["ETag"] == etag_v2
    assert p.headers["Content-Type"] == "application/json"

    data = p.json()
    assert data["displayName"] == "Иван Петров"

    _assert_uuid(p.headers["X-Request-ID"])
    _assert_no_deny_fields(data)
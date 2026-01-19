import json
import uuid
import pytest
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


def test_profile_concurrent_patch_with_stale_etag(mocker, api_client):
    """
    PROFILE CONC 051
    Второй PATCH с устаревшим ETag должен быть отвергнут (409)
    """

    profile_id = str(uuid.uuid4())
    path = PROFILES_ITEMS_PATH.format(profile_id=profile_id)

    etag_v1 = "etag-v1"
    etag_v2 = "etag-v2"

    body_v1 = {
        "profile_uuid": profile_id,
        "name": "Ivan",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
    }

    body_v2 = {**body_v1, "name": "Petr", "updated_at": "2024-01-01T10:05:00Z"}

    error_body = {
        "code": "ETAG_MISMATCH",
        "message": "Resource was modified",
        "details": [],
        "traceId": str(uuid.uuid4()),
    }

    def make_resp(status, body, etag=None):
        r = mocker.Mock()
        r.status_code = status
        r.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "X-Request-ID": body["traceId"] if "traceId" in body else str(uuid.uuid4()),
        }
        if etag:
            r.headers["ETag"] = etag
        r.json.return_value = body
        r.content = json.dumps(body).encode("utf-8")
        return r

    mocker.patch(
        "requests.get",
        return_value=make_resp(200, body_v1, etag_v1),
    )

    mocker.patch(
        "requests.patch",
        side_effect=[
            make_resp(200, body_v2, etag_v2),
            make_resp(409, error_body),
        ],
    )

    r_get = api_client.get(path)
    assert r_get.headers["ETag"] == etag_v1

    r_ok = api_client.patch(
        path,
        headers={"If-Match": etag_v1},
        json={"name": "Petr"},
    )

    assert r_ok.status_code == 200
    assert r_ok.headers["ETag"] == etag_v2
    assert r_ok.json()["name"] == "Petr"

    r_fail = api_client.patch(
        path,
        headers={"If-Match": etag_v1},
        json={"name": "Alex"},
    )

    assert r_fail.status_code == 409
    data = r_fail.json()
    assert data["traceId"] == r_fail.headers["X-Request-ID"]
    _assert_no_deny_fields(data)

import json
import uuid


PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"

DENY_FIELDS = {"debugInfo", "internalMeta", "backendOnly", "stackTrace"}


def test_xss_payload_is_sanitized_and_etag_enforced(mocker, api_client):
    profile_id = str(uuid.uuid4())

    etag_v1 = '"etag-v1"'
    etag_v2 = '"etag-v2"'

    trace_get = str(uuid.uuid4())
    trace_patch = str(uuid.uuid4())

    get_body = {
        "id": profile_id,
        "displayName": "Normal Name",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
    }

    patch_body = {
        **get_body,
        "displayName": "alert(1)",
        "updated_at": "2024-01-01T10:05:00Z",
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
    r_get.json.return_value = get_body
    r_get.content = json.dumps(get_body).encode("utf-8")

    r_patch = mocker.Mock()
    r_patch.status_code = 200
    r_patch.headers = {
        "Content-Type": "application/json",
        "ETag": etag_v2,
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_patch,
    }
    r_patch.json.return_value = patch_body
    r_patch.content = json.dumps(patch_body).encode("utf-8")

    mocker.patch("requests.get", return_value=r_get)
    mocker.patch("requests.patch", return_value=r_patch)

    r1 = api_client.get(PROFILE_PATH.format(profile_id=profile_id))
    assert r1.headers["ETag"] == etag_v1

    r2 = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        headers={"If-Match": etag_v1},
        json={"displayName": "<script>alert(1)</script>"},
    )

    assert r2.status_code == 200
    assert r2.headers["Content-Type"] == "application/json"
    assert r2.headers["Cache-Control"] == "no-store"
    assert r2.headers["Vary"] == "Authorization"

    body = r2.json()
    assert body["displayName"] == "alert(1)"
    assert "<script>" not in body["displayName"].lower()

    assert r2.headers["ETag"] == etag_v2

    uuid.UUID(r2.headers["X-Request-ID"])

    for field in DENY_FIELDS:
        assert field not in body

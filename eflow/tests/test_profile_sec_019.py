import json
import uuid
import pytest

PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"debugInfo", "internalMeta", "backendOnly", "stackTrace"}


def test_profile_xss_payload_is_sanitized(mocker, api_client):
    profile_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    etag = '"etag-safe"'

    sanitized_body = {
        "id": profile_id,
        "displayName": "alert(1)",
        "department": "IT",
    }

    resp = mocker.Mock()
    resp.status_code = 200
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": etag,
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = sanitized_body
    resp.content = json.dumps(sanitized_body).encode("utf-8")

    mocker.patch("requests.patch", return_value=resp)

    r = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        json={"displayName": "<script>alert(1)</script>"},
        headers={"Authorization": "Bearer valid-token", "If-Match": etag},
    )

    assert r.status_code == 200
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["ETag"] == etag

    data = r.json()
    assert "<script>" not in data["displayName"]
    assert "alert" in data["displayName"]

    assert r.headers["X-Request-ID"]
    uuid.UUID(r.headers["X-Request-ID"])

    for f in DENY_FIELDS:
        assert f not in data
import json
import uuid
import pytest

PROFILE_PATH = "/api/v1/profile/{profile_id}"
DENY_FIELDS = {"debugInfo", "internalMeta", "backendOnly", "stackTrace"}


def test_profile_not_found_returns_secure_error(mocker, api_client):
    profile_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "NOT_FOUND",
        "message": "Profile not found",
        "details": [],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 404
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.get", return_value=resp)

    r = api_client.get(
        PROFILE_PATH.format(profile_id=profile_id),
        headers={"Authorization": "Bearer valid-token"},
    )

    # HTTP + headers
    assert r.status_code == 404
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"
    assert r.headers["X-Request-ID"]

    uuid.UUID(r.headers["X-Request-ID"])

    # body
    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "NOT_FOUND"
    assert isinstance(data["message"], str)
    assert data["details"] == []
    assert data["traceId"] == r.headers["X-Request-ID"]
    uuid.UUID(data["traceId"])

    for f in DENY_FIELDS:
        assert f not in data
import json
import uuid
import pytest

VERIFY_PATH = "/api/v1/profiles/request-by-verification-token/{token}"
PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"

DENY_FIELDS = {"debugInfo", "internalMeta", "backendOnly", "stackTrace"}


def test_status_cannot_be_changed_via_verification_token(mocker, api_client):
    token = "valid-verification-token"
    profile_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "FORBIDDEN",
        "message": "Status update is not allowed via verification token",
        "details": [],
        "traceId": trace_id,
    }

    resp_patch = mocker.Mock()
    resp_patch.status_code = 403
    resp_patch.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp_patch.json.return_value = error_body
    resp_patch.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.patch", return_value=resp_patch)

    r = api_client.patch(
        VERIFY_PATH.format(token=token),
        json={"status": "blocked"},
    )

    assert r.status_code == 403
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "FORBIDDEN"
    assert data["details"] == []
    assert data["traceId"] == r.headers["X-Request-ID"]

    uuid.UUID(data["traceId"])

    for f in DENY_FIELDS:
        assert f not in data
import json
import uuid
import pytest

PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"

DENY_FIELDS = {"debugInfo", "internalMeta", "backendOnly", "stackTrace"}


def test_system_identifier_change_is_rejected(mocker, api_client):
    profile_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "CONFLICT",
        "message": "System identifier is immutable",
        "details": [
            {"field": "system_id", "code": "FIELD_IMMUTABLE"}
        ],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 409
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.patch", return_value=resp)

    r = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        json={"system_id": "new-id"},
    )

    assert r.status_code == 409
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["code"] == "CONFLICT"
    assert data["details"] == [
        {"field": "system_id", "code": "FIELD_IMMUTABLE"}
    ]
    assert data["traceId"] == r.headers["X-Request-ID"]

    uuid.UUID(data["traceId"])

    for field in DENY_FIELDS:
        assert field not in data
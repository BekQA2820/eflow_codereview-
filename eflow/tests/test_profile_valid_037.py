import json
import uuid


PROFILE_PATH = "/api/v1/profiles/items/{profile_id}"
DENY_FIELDS = {"debugInfo", "internalMeta", "backendOnly", "stackTrace"}


def test_profile_update_invalid_types(mocker, api_client):
    profile_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Invalid field types",
        "details": [
            {"field": "name", "code": "INVALID_TYPE"},
            {"field": "active", "code": "INVALID_TYPE"},
        ],
        "traceId": trace_id,
    }

    resp = mocker.Mock()
    resp.status_code = 400
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
        json={"name": 123, "active": "true"},
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["traceId"] == r.headers["X-Request-ID"]
    uuid.UUID(data["traceId"])

    assert data["code"] == "VALIDATION_ERROR"
    assert len(data["details"]) == 2

    for item in data["details"]:
        assert set(item.keys()) == {"field", "code"}
        assert item["code"] == "INVALID_TYPE"

    for f in DENY_FIELDS:
        assert f not in data
        assert all(f not in d for d in data["details"])
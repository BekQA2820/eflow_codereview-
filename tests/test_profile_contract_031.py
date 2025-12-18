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


def test_profile_immutable_field_cannot_be_modified(mocker, api_client):
    profile_id = str(uuid.uuid4())

    error_body = {
        "code": "IMMUTABLE_FIELD",
        "message": "Field is immutable",
        "details": [
            {"field": "employeeId", "code": "FIELD_IMMUTABLE"}
        ],
        "traceId": str(uuid.uuid4()),
    }

    resp = mocker.Mock()
    resp.status_code = 409
    resp.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": error_body["traceId"],
    }
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.request", return_value=resp)

    r = api_client.patch(
        PROFILE_PATH.format(profile_id=profile_id),
        json={"employeeId": "new-id"},
    )

    assert r.status_code == 409
    assert r.headers["Content-Type"] == "application/json"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["details"][0]["code"] == "FIELD_IMMUTABLE"

    assert data["traceId"] == r.headers["X-Request-ID"]
    _assert_uuid(data["traceId"])
    _assert_no_deny_fields(data)
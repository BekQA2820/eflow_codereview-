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


def test_profile_patch_without_if_match_returns_428(mocker, api_client):
    profile_id = str(uuid.uuid4())

    error_body = {
        "code": "PRECONDITION_REQUIRED",
        "message": "If-Match header is required",
        "details": [],
        "traceId": str(uuid.uuid4()),
    }

    resp = mocker.Mock()
    resp.status_code = 428
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
        json={"displayName": "Ivan"},
    )

    assert r.status_code == 428
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["details"] == []

    assert data["traceId"] == r.headers["X-Request-ID"]
    _assert_uuid(data["traceId"])
    _assert_no_deny_fields(data)
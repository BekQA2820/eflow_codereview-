import json
import uuid

PROFILES_ITEMS_PATH = "/api/v1/profiles/items/{profile_id}"
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


def test_profile_patch_rejects_unknown_fields(mocker, api_client):
    profile_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Field not allowed",
        "details": [{"field": "unexpectedField", "code": "FIELD_NOT_ALLOWED"}],
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

    mocker.patch("requests.request", return_value=resp)

    r = api_client.patch(
        PROFILES_ITEMS_PATH.format(profile_id=profile_id),
        json={
            "name": "Petr",
            "unexpectedField": "boom",
        },
        headers={"If-Match": "etag-v1"},
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["details"] == [{"field": "unexpectedField", "code": "FIELD_NOT_ALLOWED"}]
    assert body["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(body["traceId"])
    _assert_no_deny_fields(body)
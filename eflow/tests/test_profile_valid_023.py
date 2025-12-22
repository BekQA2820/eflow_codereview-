import json
import uuid

PROFILES_CREATE_PATH = "/api/v1/profiles/items"
DENY_FIELDS = {"internalMeta", "debugInfo", "backendOnly"}


def _assert_uuid(v: str):
    uuid.UUID(v)


def _assert_no_deny_fields(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in DENY_FIELDS
            _assert_no_deny_fields(v)
    elif isinstance(obj, list):
        for i in obj:
            _assert_no_deny_fields(i)


def test_profile_pharmacist_requires_subject_rf(mocker, api_client):
    trace_id = str(uuid.uuid4())

    error = {
        "code": "VALIDATION_ERROR",
        "message": "Required field missing",
        "details": [{"field": "subject_rf", "code": "REQUIRED"}],
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
    resp.json.return_value = error
    resp.content = json.dumps(error).encode("utf-8")

    mocker.patch("requests.request", return_value=resp)

    r = api_client.post(
        PROFILES_CREATE_PATH,
        json={
            "role": "PHARMACIST",
            "name": "Ivan",
            "surname": "Petrov",
            "phone": "+79990000001",
            "consent_processing": True,
            "consent_communication": True,
        },
    )

    assert r.status_code == 400

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["details"] == [{"field": "subject_rf", "code": "REQUIRED"}]
    assert body["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(body["traceId"])
    _assert_no_deny_fields(body)
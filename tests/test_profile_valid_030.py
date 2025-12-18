import json
import uuid

PROFILES_CREATE_PATH = "/api/v1/profiles/items"
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


def test_profile_requires_consent_communication(mocker, api_client):
    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Consent is required",
        "details": [{"field": "consent_communication", "code": "REQUIRED"}],
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

    r = api_client.post(
        PROFILES_CREATE_PATH,
        json={
            "role": "HCP",
            "name": "Ivan",
            "surname": "Ivanov",
            "phone": "+79990002001",
            "subject_rf": "77",
            "specialty_sz": "THERAPIST",
            "consent_processing": "Yes",
        },
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    body = r.json()
    assert set(body.keys()) == {"code", "message", "details", "traceId"}
    assert body["details"] == [{"field": "consent_communication", "code": "REQUIRED"}]
    assert body["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(body["traceId"])
    _assert_no_deny_fields(body)
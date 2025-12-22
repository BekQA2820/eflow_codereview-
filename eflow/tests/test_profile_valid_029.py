import json
import uuid

PROFILES_CREATE_PATH = "/api/v1/profiles/items"
DENY_FIELDS = {"internalMeta", "debugInfo", "backendOnly"}


def _assert_uuid(value):
    uuid.UUID(value)


def _assert_no_deny_fields(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in DENY_FIELDS
            _assert_no_deny_fields(v)
    elif isinstance(obj, list):
        for i in obj:
            _assert_no_deny_fields(i)


def test_profile_requires_consent_processing(mocker, api_client):
    trace_id = str(uuid.uuid4())

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Consent is required",
        "details": [{"field": "consent_processing", "code": "REQUIRED"}],
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
            "name": "Pavel",
            "surname": "Kuznetsov",
            "phone": "+79990001003",
            "subject_rf": "77",
            "specialty_sz": "CARDIOLOGIST",
            "consent_communication": "Yes",
        },
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert data["details"] == [{"field": "consent_processing", "code": "REQUIRED"}]
    assert data["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(data["traceId"])
    _assert_no_deny_fields(data)
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


def test_profile_hcp_subject_rf_required(mocker, api_client):
    trace_id = str(uuid.uuid4())

    error_body = {
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
    resp.json.return_value = error_body
    resp.content = json.dumps(error_body).encode("utf-8")

    mocker.patch("requests.request", return_value=resp)

    r = api_client.post(
        PROFILES_CREATE_PATH,
        json={
            "role": "HCP",
            "name": "Ivan",
            "surname": "Petrov",
            "phone": "+79990001001",
            "specialty_sz": "THERAPIST",
            "consent_processing": "Yes",
            "consent_communication": "Yes",
        },
    )

    assert r.status_code == 400
    assert r.headers["Content-Type"] == "application/json"
    assert r.headers["Cache-Control"] == "no-store"
    assert r.headers["Vary"] == "Authorization"

    data = r.json()
    assert set(data.keys()) == {"code", "message", "details", "traceId"}
    assert data["details"] == [{"field": "subject_rf", "code": "REQUIRED"}]
    assert data["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(data["traceId"])
    _assert_no_deny_fields(data)
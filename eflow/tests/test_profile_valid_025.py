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


def test_profile_hcp_requires_specialty_sz(mocker, api_client):
    trace_id = str(uuid.uuid4())

    error = {
        "code": "VALIDATION_ERROR",
        "message": "Required field missing",
        "details": [{"field": "specialty_sz", "code": "REQUIRED"}],
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
            "role": "HCP",
            "name": "Oleg",
            "surname": "Ivanov",
            "phone": "+79990000003",
            "subject_rf": "77",
            "consent_processing": True,
            "consent_communication": True,
        },
    )

    assert r.status_code == 400

    body = r.json()
    assert body["details"] == [{"field": "specialty_sz", "code": "REQUIRED"}]
    assert body["traceId"] == r.headers["X-Request-ID"]

    _assert_uuid(body["traceId"])
    _assert_no_deny_fields(body)
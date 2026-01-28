import pytest
import uuid

TARGET_PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{TARGET_PROFILE_ID}"

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "requiredroles", "requiredpermissions",
    "email", "phone", "first_name", "last_name"
}


@pytest.mark.integration
def test_profile_negative_010_forbidden_no_leaks(api_client, auth_header):
    response = api_client.get(
        PATH,
        headers=auth_header
    )

    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    vary = response.headers.get("Vary", "")
    assert "Authorization" in vary

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert "trace_id" in data or "traceId" in data

    error_msg = data.get("message", "").lower()
    assert TARGET_PROFILE_ID not in error_msg
    assert "not found" not in error_msg
    assert "exists" not in error_msg

    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    assert "prid" not in raw_low
    assert "12345" not in raw_low
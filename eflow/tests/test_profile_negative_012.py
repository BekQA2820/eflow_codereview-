import pytest
import uuid

PROFILE_ID_B = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH_B = f"/api/v1/employee-profiles/{PROFILE_ID_B}"

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "<html", "email", "phone", "first_name",
    "last_name", "roles", "permissions", "profile_uuid"
}


@pytest.mark.integration
def test_profile_negative_012_horizontal_escalation(api_client, auth_header):
    response = api_client.get(
        PATH_B,
        headers=auth_header
    )

    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert "message" in data

    trace_id = data.get("traceId")
    x_request_id = response.headers.get("X-Request-ID")
    assert trace_id is not None
    assert x_request_id is not None
    assert trace_id in [x_request_id, f"tr-{x_request_id}"]

    error_msg = data.get("message", "").lower()
    assert PROFILE_ID_B not in error_msg
    assert "user b" not in error_msg

    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    assert "prid" not in raw_low
    assert "12345" not in raw_low
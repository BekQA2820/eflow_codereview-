import pytest
import uuid

PROFILE_PATH = "/api/v1/employee-profiles/3fa85f64-5717-4562-b3fc-2c963f66afa6"

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "<html", "sql", "debug", "email", "phone"
}


@pytest.mark.integration
def test_profile_negative_001_unauthorized(api_client):
    response = api_client.get(
        PROFILE_PATH,
        headers={}
    )

    assert response.status_code == 401
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] is not None
    assert isinstance(data["code"], str)
    assert "message" in data
    assert isinstance(data.get("details"), list)

    trace_id = data.get("traceId")
    x_request_id = response.headers.get("X-Request-ID")
    assert trace_id is not None
    assert x_request_id is not None

    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    assert "prid" not in raw_low
    assert "12345" not in raw_low
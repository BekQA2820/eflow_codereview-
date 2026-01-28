import pytest
import uuid

NON_EXISTENT_ID = "00000000-0000-0000-0000-000000000000"
PATH = f"/api/v1/employee-profiles/{NON_EXISTENT_ID}"

DENY_FIELDS = {
    "s3", "registry", "database", "sql", "find", "search",
    "internalflags", "stacktrace", "exception", "<html",
    "requiredroles", "configsource"
}


@pytest.mark.integration
def test_profile_negative_011_not_found(api_client, auth_header):
    response = api_client.get(
        PATH,
        headers=auth_header
    )

    assert response.status_code == 404
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    vary = response.headers.get("Vary", "")
    assert "Authorization" in vary

    data = response.json()
    assert data["code"] == "NOT_FOUND"
    assert "message" in data
    assert "traceId" in data or "trace_id" in data

    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    assert "prid" not in raw_low
    assert "12345" not in raw_low
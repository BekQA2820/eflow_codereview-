import json
import pytest

from responses import make_json_response


DENY_TEXT_TOKENS = {
    "internalflags",
    "internalid",
    "requiredpermissions",
    "configsource",
    "internalmeta",
    "debuginfo",
    "stacktrace",
    "exception",
    "<html",
}


@pytest.mark.integration
def test_cron_profile_014_idempotent_response(mocker, api_client):
    body = {
        "profile_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "displayName": "John Doe",
        "email": "john.doe@example.com",
        "widgets": [{"id": "w1", "name": "Widget One"}],
    }

    resp1 = make_json_response(status=200, body=body, headers={"X-Request-ID": "trace-200-run-1"})
    resp2 = make_json_response(status=200, body=body, headers={"X-Request-ID": "trace-200-run-2"})

    mocker.patch("requests.request", side_effect=[resp1, resp2])

    first = api_client.get("/api/v1/cron/profile", headers={"X-Roles": json.dumps(["admin"])})
    second = api_client.get("/api/v1/cron/profile", headers={"X-Roles": json.dumps(["admin"])})

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json() == second.json()

    body_text = second.text.lower()
    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

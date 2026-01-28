import json
import uuid
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
def test_cron_profile_013_success_with_valid_roles(mocker, api_client):
    body = {
        "profile_uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "displayName": "John Doe",
        "email": "john.doe@example.com",
        "widgets": [
            {"id": "w1", "name": "Widget One"},
            {"id": "w2", "name": "Widget Two"},
        ],
    }

    resp = make_json_response(
        status=200,
        body=body,
        headers={"X-Request-ID": "trace-200-cron-profile"},
    )

    mocker.patch("requests.request", return_value=resp)

    response = api_client.get(
        "/api/v1/cron/profile",
        headers={"X-Roles": json.dumps(["admin"])},
    )

    assert response.status_code == 200

    data = response.json()
    uuid.UUID(data["profile_uuid"])
    assert isinstance(data.get("displayName"), str) and data["displayName"]
    assert isinstance(data.get("email"), str) and data["email"]
    assert isinstance(data.get("widgets"), list)

    body_text = response.text.lower()
    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

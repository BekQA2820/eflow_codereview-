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
def test_cron_profile_015_no_partial_data_on_access_denied(mocker, api_client):
    resp = make_json_response(
        status=403,
        body={
            "code": "FORBIDDEN",
            "message": "access denied",
            "details": [],
            "traceId": "trace-403-no-partial",
        },
        headers={"X-Request-ID": "trace-403-no-partial"},
    )

    mocker.patch("requests.request", return_value=resp)

    response = api_client.get(
        "/api/v1/cron/profile",
        headers={"X-Roles": json.dumps(["viewer"])},
    )

    assert response.status_code == 403

    data = response.json()
    assert data.get("code") == "FORBIDDEN"
    assert isinstance(data.get("message"), str) and data["message"]

    body_text = response.text.lower()
    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

    forbidden_profile_tokens = {"displayname", "email", "widgets", "profile_uuid", "profile_id"}
    for token in forbidden_profile_tokens:
        assert token not in body_text

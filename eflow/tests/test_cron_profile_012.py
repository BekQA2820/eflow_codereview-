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
def test_cron_profile_012_not_found_when_profile_uuid_missing(mocker, api_client):
    resp = make_json_response(
        status=404,
        body={
            "code": "NOT_FOUND",
            "message": "profile not found",
            "details": [],
            "traceId": "trace-404-profile-missing",
        },
        headers={"X-Request-ID": "trace-404-profile-missing"},
    )

    mocker.patch("requests.request", return_value=resp)

    response = api_client.get(
        "/api/v1/cron/profile",
        headers={"X-Roles": json.dumps(["admin"])},
    )

    assert response.status_code == 404

    data = response.json()
    assert data.get("code") == "NOT_FOUND"
    assert isinstance(data.get("message"), str) and data["message"]

    body_text = response.text.lower()
    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

    forbidden_profile_tokens = {"profile_uuid", "profile_id", "displayname", "email", "widgets"}
    for token in forbidden_profile_tokens:
        assert token not in body_text

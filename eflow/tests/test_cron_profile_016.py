import json

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


def test_cron_profile_016_not_found_when_profile_id_missing(mocker, api_client):
    resp = make_json_response(
        status=404,
        body={
            "code": "NOT_FOUND",
            "message": "profile not found",
            "details": [],
            "traceId": "trace-404-profile-id-missing",
        },
        headers={"X-Request-ID": "trace-404-profile-id-missing"},
    )

    mocker.patch("requests.Session.request", return_value=resp)

    response = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Roles": json.dumps(["admin"]),
            "X-Profile-Id": "00000000-0000-0000-0000-000000000000",
        },
    )

    assert response.status_code == 404

    data = response.json()
    assert "code" in data
    assert "message" in data
    assert isinstance(data["message"], str) and data["message"]

    body_text = response.text.lower()

    forbidden_profile_tokens = {
        "displayname",
        "email",
        "widgets",
        "profile_id",
    }
    for token in forbidden_profile_tokens:
        assert token not in body_text

    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

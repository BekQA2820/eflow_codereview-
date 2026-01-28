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


def test_cron_profile_024_widgets_absent_on_forbidden(mocker, api_client):
    resp = make_json_response(
        status=403,
        body={
            "code": "FORBIDDEN",
            "message": "access denied",
            "details": [],
            "traceId": "trace-403-no-widgets",
        },
        headers={"X-Request-ID": "trace-403-no-widgets"},
    )

    mocker.patch("requests.Session.request", return_value=resp)

    response = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Roles": json.dumps(["viewer"]),
            "X-Profile-Id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
    )

    assert response.status_code == 403

    data = response.json()
    assert "code" in data
    assert "message" in data

    body_text = response.text.lower()

    forbidden_profile_tokens = {
        "widgets",
        "displayname",
        "email",
        "profile_id",
    }
    for token in forbidden_profile_tokens:
        assert token not in body_text

    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

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


def test_cron_profile_032_email_stable_on_repeated_success(mocker, api_client):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    roles = ["admin"]

    body = {
        "code": "SUCCESS",
        "message": "ok",
        "profile_id": profile_id,
        "displayName": "John Doe",
        "email": "john.doe@example.com",
        "widgets": [
            {"id": "w1", "name": "Widget One"},
        ],
    }

    resp_first = make_json_response(
        status=200,
        body=body,
        headers={"X-Request-ID": "trace-200-email-stable-1"},
    )
    resp_second = make_json_response(
        status=200,
        body=body,
        headers={"X-Request-ID": "trace-200-email-stable-2"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp_first, resp_second],
    )

    first = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Roles": json.dumps(roles),
            "X-Profile-Id": profile_id,
        },
    )
    second = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Roles": json.dumps(roles),
            "X-Profile-Id": profile_id,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200

    data_first = first.json()
    data_second = second.json()

    assert "code" in data_first and "message" in data_first
    assert "code" in data_second and "message" in data_second

    assert data_first["email"] == data_second["email"]

    body_text = second.text.lower()
    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

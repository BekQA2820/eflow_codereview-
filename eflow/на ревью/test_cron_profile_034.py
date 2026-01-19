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


def test_cron_profile_034_idempotent_403_on_repeated_runs(mocker, api_client):
    body = {
        "code": "FORBIDDEN",
        "message": "access denied",
        "details": [],
        "traceId": "trace-403-idempotent",
    }

    resp_first = make_json_response(
        status=403,
        body=body,
        headers={"X-Request-ID": "trace-403-idempotent"},
    )
    resp_second = make_json_response(
        status=403,
        body=body,
        headers={"X-Request-ID": "trace-403-idempotent"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp_first, resp_second],
    )

    first = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Roles": json.dumps(["viewer"]),
            "X-Profile-Id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
    )
    second = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Roles": json.dumps(["viewer"]),
            "X-Profile-Id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        },
    )

    assert first.status_code == 403
    assert second.status_code == 403

    data_first = first.json()
    data_second = second.json()

    assert data_first == data_second

    body_text = second.text.lower()

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

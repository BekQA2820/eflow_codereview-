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


def test_cron_profile_037_conflict_state_returns_409_idempotent(mocker, api_client):
    body = {
        "code": "CONFLICT",
        "message": "profile is in conflicting state",
        "details": [],
        "traceId": "trace-409-logical-conflict",
    }

    resp_first = make_json_response(
        status=409,
        body=body,
        headers={"X-Request-ID": "trace-409-logical-conflict"},
    )
    resp_second = make_json_response(
        status=409,
        body=body,
        headers={"X-Request-ID": "trace-409-logical-conflict"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp_first, resp_second],
    )

    first = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "X-Roles": json.dumps(["admin"]),
        },
    )
    second = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "X-Roles": json.dumps(["admin"]),
        },
    )

    assert first.status_code == 409
    assert second.status_code == 409

    data_first = first.json()
    data_second = second.json()

    assert data_first == data_second
    assert "code" in data_first
    assert "message" in data_first

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

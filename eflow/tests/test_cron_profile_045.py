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


def test_cron_profile_045_idempotent_403_without_side_effects(mocker, api_client):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    body = {
        "code": "FORBIDDEN",
        "message": "access denied",
        "details": [],
        "traceId": "trace-403-idempotent-045",
    }

    resp1 = make_json_response(
        status=403,
        body=body,
        headers={"X-Request-ID": "trace-403-idempotent-045"},
    )
    resp2 = make_json_response(
        status=403,
        body=body,
        headers={"X-Request-ID": "trace-403-idempotent-045"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp1, resp2],
    )

    first = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
            "X-Roles": json.dumps([]),
        },
    )
    second = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
            "X-Roles": json.dumps([]),
        },
    )

    assert first.status_code == 403
    assert second.status_code == 403

    data_first = first.json()
    data_second = second.json()

    assert data_first == data_second
    assert "code" in data_first
    assert "message" in data_first
    assert isinstance(data_first["message"], str) and data_first["message"]

    body_text = second.text.lower()

    forbidden_profile_tokens = {
        "displayname",
        "email",
        "widgets",
        "roles",
        "profile_id",
    }
    for token in forbidden_profile_tokens:
        assert token not in body_text

    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

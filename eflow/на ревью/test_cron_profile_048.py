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


def test_cron_profile_048_idempotent_409_conflict(mocker, api_client):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    body = {
        "code": "CONFLICT",
        "message": "profile version conflict",
        "details": [],
        "traceId": "trace-409-idempotent-048",
    }

    resp1 = make_json_response(
        status=409,
        body=body,
        headers={"X-Request-ID": "trace-409-idempotent-048"},
    )
    resp2 = make_json_response(
        status=409,
        body=body,
        headers={"X-Request-ID": "trace-409-idempotent-048"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp1, resp2],
    )

    first = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
            "X-Roles": json.dumps(["admin"]),
        },
    )
    second = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
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
    assert isinstance(data_first["message"], str) and data_first["message"]

    body_text = second.text.lower()

    forbidden_profile_tokens = {
        "displayname",
        "email",
        "roles",
        "widgets",
        "profile_id",
    }
    for token in forbidden_profile_tokens:
        assert token not in body_text

    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

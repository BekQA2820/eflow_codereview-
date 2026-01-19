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


def test_cron_profile_046_version_conflict_after_success(mocker, api_client):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    success_body = {
        "code": "SUCCESS",
        "message": "ok",
        "profile_id": profile_id,
        "displayName": "John Doe",
        "email": "john.doe@example.com",
        "widgets": [
            {"id": "w1", "name": "Widget One"},
            {"id": "w2", "name": "Widget Two"},
        ],
    }

    conflict_body = {
        "code": "CONFLICT",
        "message": "profile version conflict",
        "details": [],
        "traceId": "trace-409-version-conflict",
    }

    resp_ok = make_json_response(
        status=200,
        body=success_body,
        headers={"X-Request-ID": "trace-200-initial"},
    )
    resp_conflict_1 = make_json_response(
        status=409,
        body=conflict_body,
        headers={"X-Request-ID": "trace-409-version-conflict"},
    )
    resp_conflict_2 = make_json_response(
        status=409,
        body=conflict_body,
        headers={"X-Request-ID": "trace-409-version-conflict"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp_ok, resp_conflict_1, resp_conflict_2],
    )

    first = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
            "X-Roles": json.dumps(["admin"]),
        },
    )

    assert first.status_code == 200
    data_ok = first.json()
    assert "code" in data_ok and "message" in data_ok

    second = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
            "X-Roles": json.dumps(["admin"]),
        },
    )
    third = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
            "X-Roles": json.dumps(["admin"]),
        },
    )

    assert second.status_code == 409
    assert third.status_code == 409

    data_conflict_1 = second.json()
    data_conflict_2 = third.json()

    assert data_conflict_1 == data_conflict_2
    assert "code" in data_conflict_1
    assert "message" in data_conflict_1

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

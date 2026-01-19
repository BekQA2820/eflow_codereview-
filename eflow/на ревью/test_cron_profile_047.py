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


def test_cron_profile_047_no_data_mutation_on_409_conflict(mocker, api_client):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    roles = ["admin"]

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
        "traceId": "trace-409-no-mutation",
    }

    resp_ok = make_json_response(
        status=200,
        body=success_body,
        headers={"X-Request-ID": "trace-200-initial-state"},
    )
    resp_conflict_1 = make_json_response(
        status=409,
        body=conflict_body,
        headers={"X-Request-ID": "trace-409-no-mutation"},
    )
    resp_conflict_2 = make_json_response(
        status=409,
        body=conflict_body,
        headers={"X-Request-ID": "trace-409-no-mutation"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp_ok, resp_conflict_1, resp_conflict_2],
    )

    first = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
            "X-Roles": json.dumps(roles),
        },
    )
    assert first.status_code == 200
    data_initial = first.json()
    assert "code" in data_initial and "message" in data_initial

    second = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
            "X-Roles": json.dumps(roles),
        },
    )
    third = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id,
            "X-Roles": json.dumps(roles),
        },
    )

    assert second.status_code == 409
    assert third.status_code == 409

    conflict_data_1 = second.json()
    conflict_data_2 = third.json()

    assert conflict_data_1 == conflict_data_2
    assert "code" in conflict_data_1
    assert "message" in conflict_data_1

    # Проверяем, что конфликтные ответы не содержат доменных данных
    conflict_text = second.text.lower()
    forbidden_profile_tokens = {
        "displayname",
        "email",
        "widgets",
        "roles",
        "profile_id",
    }
    for token in forbidden_profile_tokens:
        assert token not in conflict_text

    for token in DENY_TEXT_TOKENS:
        assert token not in conflict_text

    # Проверяем, что сохраненное успешное состояние не "протекло" и не изменилось
    assert data_initial["displayName"] == "John Doe"
    assert data_initial["email"] == "john.doe@example.com"
    assert data_initial["widgets"] == [
        {"id": "w1", "name": "Widget One"},
        {"id": "w2", "name": "Widget Two"},
    ]

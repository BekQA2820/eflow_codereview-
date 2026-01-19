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
    "not found",
    "does not exist",
    "unknown profile",
}


def test_cron_profile_044_403_does_not_confirm_profile_existence(mocker, api_client):
    profile_id_existing = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    profile_id_missing = "11111111-2222-3333-4444-555555555555"

    body = {
        "code": "FORBIDDEN",
        "message": "access denied",
        "details": [],
        "traceId": "trace-403-uniform",
    }

    resp_a = make_json_response(
        status=403,
        body=body,
        headers={"X-Request-ID": "trace-403-uniform-a"},
    )
    resp_b = make_json_response(
        status=403,
        body=body,
        headers={"X-Request-ID": "trace-403-uniform-b"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp_a, resp_b],
    )

    response_existing = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id_existing,
            "X-Roles": json.dumps([]),
        },
    )

    response_missing = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id_missing,
            "X-Roles": json.dumps([]),
        },
    )

    assert response_existing.status_code == 403
    assert response_missing.status_code == 403

    data_existing = response_existing.json()
    data_missing = response_missing.json()

    assert "code" in data_existing
    assert "message" in data_existing
    assert "code" in data_missing
    assert "message" in data_missing

    # структура ошибок идентична, допускается различие traceId
    comparable_existing = {k: v for k, v in data_existing.items() if k != "traceId"}
    comparable_missing = {k: v for k, v in data_missing.items() if k != "traceId"}
    assert comparable_existing == comparable_missing

    body_text_existing = response_existing.text.lower()
    body_text_missing = response_missing.text.lower()

    forbidden_profile_tokens = {
        "displayname",
        "email",
        "widgets",
        "roles",
        "profile_id",
    }

    for token in forbidden_profile_tokens:
        assert token not in body_text_existing
        assert token not in body_text_missing

    for token in DENY_TEXT_TOKENS:
        assert token not in body_text_existing
        assert token not in body_text_missing

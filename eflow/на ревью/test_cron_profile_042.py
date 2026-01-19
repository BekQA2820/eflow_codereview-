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


def test_cron_profile_042_idempotent_404_for_unknown_profile_id(mocker, api_client):
    body = {
        "code": "NOT_FOUND",
        "message": "profile not found",
        "details": [],
        "traceId": "trace-404-idempotent",
    }

    resp1 = make_json_response(
        status=404,
        body=body,
        headers={"X-Request-ID": "trace-404-idempotent"},
    )
    resp2 = make_json_response(
        status=404,
        body=body,
        headers={"X-Request-ID": "trace-404-idempotent"},
    )
    resp3 = make_json_response(
        status=404,
        body=body,
        headers={"X-Request-ID": "trace-404-idempotent"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp1, resp2, resp3],
    )

    responses = []
    for _ in range(3):
        r = api_client.get(
            "/api/v1/cron/profile",
            headers={
                "X-Profile-Id": "00000000-0000-0000-0000-000000000000",
                "X-Roles": json.dumps(["admin"]),
            },
        )
        responses.append(r)

    for r in responses:
        assert r.status_code == 404

    data_1 = responses[0].json()
    data_2 = responses[1].json()
    data_3 = responses[2].json()

    assert data_1 == data_2 == data_3
    assert "code" in data_1
    assert "message" in data_1

    body_text = responses[0].text.lower()

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

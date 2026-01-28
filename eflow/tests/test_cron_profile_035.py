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


def test_cron_profile_035_403_and_404_are_not_masked(mocker, api_client):
    resp_404 = make_json_response(
        status=404,
        body={
            "code": "NOT_FOUND",
            "message": "profile not found",
            "details": [],
            "traceId": "trace-404-profile-missing",
        },
        headers={"X-Request-ID": "trace-404-profile-missing"},
    )

    resp_403 = make_json_response(
        status=403,
        body={
            "code": "FORBIDDEN",
            "message": "access denied",
            "details": [],
            "traceId": "trace-403-no-access",
        },
        headers={"X-Request-ID": "trace-403-no-access"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp_404, resp_403],
    )

    not_found = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": "00000000-0000-0000-0000-000000000000",
            "X-Roles": json.dumps(["admin"]),
        },
    )

    forbidden = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "X-Roles": json.dumps(["viewer"]),
        },
    )

    assert not_found.status_code == 404
    assert forbidden.status_code == 403

    data_404 = not_found.json()
    data_403 = forbidden.json()

    assert "code" in data_404 and "message" in data_404
    assert "code" in data_403 and "message" in data_403

    body_404 = not_found.text.lower()
    body_403 = forbidden.text.lower()

    forbidden_profile_tokens = {
        "displayname",
        "email",
        "widgets",
        "profile_id",
    }

    for token in forbidden_profile_tokens:
        assert token not in body_404
        assert token not in body_403

    for token in DENY_TEXT_TOKENS:
        assert token not in body_404
        assert token not in body_403

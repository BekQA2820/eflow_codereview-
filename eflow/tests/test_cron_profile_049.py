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
    "previously existed",
    "was deleted",
}


def test_cron_profile_049_not_found_when_profile_absent(mocker, api_client):
    body = {
        "code": "NOT_FOUND",
        "message": "profile not found",
        "details": [],
        "traceId": "trace-404-profile-absent-049",
    }

    resp1 = make_json_response(
        status=404,
        body=body,
        headers={"X-Request-ID": "trace-404-profile-absent-049"},
    )
    resp2 = make_json_response(
        status=404,
        body=body,
        headers={"X-Request-ID": "trace-404-profile-absent-049"},
    )

    mocker.patch(
        "requests.Session.request",
        side_effect=[resp1, resp2],
    )

    profile_id_missing = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"

    first = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id_missing,
            "X-Roles": json.dumps(["admin"]),
        },
    )
    second = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": profile_id_missing,
            "X-Roles": json.dumps(["admin"]),
        },
    )

    assert first.status_code == 404
    assert second.status_code == 404

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

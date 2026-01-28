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


def test_cron_profile_019_success_with_multiple_allowed_roles(mocker, api_client):
    roles = ["admin", "manager"]

    body = {
        "code": "SUCCESS",
        "message": "ok",
        "profile_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "displayName": "John Doe",
        "email": "john.doe@example.com",
        "roles": roles,
        "widgets": [
            {"id": "w1", "name": "Widget One"},
            {"id": "w2", "name": "Widget Two"},
        ],
    }

    resp = make_json_response(
        status=200,
        body=body,
        headers={"X-Request-ID": "trace-200-multi-roles"},
    )

    mocker.patch("requests.Session.request", return_value=resp)

    response = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Roles": json.dumps(roles),
            "X-Profile-Id": body["profile_id"],
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "code" in data
    assert "message" in data
    assert data["roles"] == roles

    body_text = response.text.lower()
    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

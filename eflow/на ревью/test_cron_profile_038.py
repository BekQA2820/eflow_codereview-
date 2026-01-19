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


def test_cron_profile_038_no_side_data_on_409_conflict(mocker, api_client):
    resp = make_json_response(
        status=409,
        body={
            "code": "CONFLICT",
            "message": "profile conflict detected",
            "details": [],
            "traceId": "trace-409-no-side-data",
        },
        headers={"X-Request-ID": "trace-409-no-side-data"},
    )

    mocker.patch("requests.Session.request", return_value=resp)

    response = api_client.get(
        "/api/v1/cron/profile",
        headers={
            "X-Profile-Id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "X-Roles": json.dumps(["admin"]),
        },
    )

    assert response.status_code == 409

    data = response.json()
    assert "code" in data
    assert "message" in data
    assert isinstance(data["message"], str) and data["message"]

    body_text = response.text.lower()

    forbidden_profile_tokens = {
        "widgets",
        "displayname",
        "email",
        "profile_id",
    }
    for token in forbidden_profile_tokens:
        assert token not in body_text

    for token in DENY_TEXT_TOKENS:
        assert token not in body_text

import json
import uuid
import requests
from unittest.mock import patch


def _make_403_response() -> requests.Response:
    r = requests.Response()
    r.status_code = 403
    r.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()),
    }
    body = {
        "code": "FORBIDDEN",
        "message": "insufficient role",
        "traceId": r.headers["X-Request-ID"],
    }
    payload = json.dumps(body)
    r._content = payload.encode("utf-8")
    return r


def test_cron_profile_011_forbidden_when_role_insufficient(api_client):
    with patch(
        "requests.Session.request",
        return_value=_make_403_response(),
    ):
        response = api_client.get(
            "/api/v1/cron/profile",
            headers={"X-Roles": json.dumps(["viewer"])},
        )

    assert response.status_code == 403

    body = response.text.lower()

    forbidden_fields = {
        "profile_uuid",
        "profile_id",
        "displayname",
        "email",
        "widgets",
    }

    for field in forbidden_fields:
        assert field not in body

    deny_fields = {
        "stacktrace",
        "exception",
        "internalmeta",
        "<html",
    }

    for field in deny_fields:
        assert field not in body

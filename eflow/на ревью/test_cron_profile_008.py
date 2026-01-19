import json
import uuid
import requests
from unittest.mock import patch


def _make_500_response() -> requests.Response:
    r = requests.Response()
    r.status_code = 500
    r.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()),
    }
    body = {
        "code": "INTERNAL_ERROR",
        "message": "external service failure",
        "traceId": r.headers["X-Request-ID"],
    }
    payload = json.dumps(body)
    r._content = payload.encode("utf-8")
    return r


def _make_200_response(profile_id: str) -> requests.Response:
    r = requests.Response()
    r.status_code = 200
    r.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()),
    }
    body = {
        "data": {
            "type": "employee_profile",
            "id": profile_id,
            "version_type": "1",
            "attributes": {
                "prid": "12345",
                "email": "example@domain.com",
                "location": "Office",
                "acc_type": "Staff",
            },
            "relationships": {
                "person": {
                    "data": {
                        "type": "ps_person",
                        "id": str(uuid.uuid4()),
                    }
                }
            },
        }
    }
    payload = json.dumps(body)
    r._content = payload.encode("utf-8")
    return r


def test_cron_profile_008_partial_external_api_failure(api_client):
    responses = [
        _make_200_response("3fa85f64-5717-4562-b3fc-2c963f66afa6"),
        _make_500_response(),
        _make_200_response("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    ]

    with patch(
        "requests.Session.request",
        side_effect=responses,
    ):
        response = api_client.get("/api/v1/cron/profile")

    assert response.status_code == 200

    body = response.text.lower()

    deny_fields = {
        "stacktrace",
        "exception",
        "internalmeta",
        "<html",
    }

    for field in deny_fields:
        assert field not in body

import json
import uuid
import pytest
import requests
from unittest.mock import patch


def _make_404_response() -> requests.Response:
    r = requests.Response()
    r.status_code = 404
    r.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()),
    }
    body = {
        "code": "NOT_FOUND",
        "message": "employee_profile not found",
        "traceId": r.headers["X-Request-ID"],
    }
    payload = json.dumps(body)
    r._content = payload.encode("utf-8")
    return r


def _make_200_response() -> requests.Response:
    r = requests.Response()
    r.status_code = 200
    r.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()),
    }
    r._content = b"{}"
    return r


def test_cron_profile_007_employee_profile_404_is_handled(api_client):
    with patch(
        "requests.Session.request",
        side_effect=[
            _make_404_response(),
            _make_200_response(),
        ],
    ):
        response = api_client.get("/api/v1/cron/profile")

    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith("application/json")

    body_text = response.text.lower()

    deny_fields = {
        "stacktrace",
        "exception",
        "internalmeta",
        "<html",
    }

    for field in deny_fields:
        assert field not in body_text

import json
import uuid
import pytest
import requests
from unittest.mock import patch


def _make_response(body: dict) -> requests.Response:
    r = requests.Response()
    r.status_code = 200
    r.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()),
    }
    payload = json.dumps(body)
    r._content = payload.encode("utf-8")
    return r


def test_cron_profile_006_checksum_not_changed_when_relationships_order_differs(api_client):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    response_1 = {
        "data": {
            "type": "employee_profile",
            "id": profile_id,
            "version_type": "1",
            "attributes": {
                "prid": "12345",
                "email": "example@domain.com",
                "location": "Office",
                "acc_type": "Staff"
            },
            "relationships": {
                "positions": {
                    "data": [
                        {"type": "ps_position", "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"},
                        {"type": "ps_position", "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}
                    ]
                }
            }
        }
    }

    response_2 = {
        "data": {
            "type": "employee_profile",
            "id": profile_id,
            "version_type": "1",
            "attributes": {
                "prid": "12345",
                "email": "example@domain.com",
                "location": "Office",
                "acc_type": "Staff"
            },
            "relationships": {
                "positions": {
                    "data": [
                        {"type": "ps_position", "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"},
                        {"type": "ps_position", "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}
                    ]
                }
            }
        }
    }

    with patch(
        "requests.Session.request",
        side_effect=[
            _make_response(response_1),
            _make_response(response_2),
        ],
    ):
        first = api_client.get("/api/v1/cron/profile")
        second = api_client.get("/api/v1/cron/profile")

    assert first.status_code == 200
    assert second.status_code == 200

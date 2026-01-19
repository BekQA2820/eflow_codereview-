import json
import uuid
import hashlib
import requests
from datetime import datetime, timezone

EMPLOYEE_PROFILE_PATH = "/employee-profiles/{profile_id}"
CRON_SYNC_PATH = "/internal/cron/profile-sync/{profile_id}"


def _canonical_checksum(data: dict) -> bytes:
    payload = {
        "type": data["data"]["type"],
        "version_type": data["data"]["version_type"],
        "attributes": data["data"]["attributes"],
        "relationships": {
            k: {
                "data": v.get("data")
            }
            for k, v in data["data"].get("relationships", {}).items()
            if "data" in v
        },
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).digest()


def _make_response(status: int, body: dict):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(body).encode()
    r.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()),
    }
    return r


def test_cron_profile_003(mocker, api_client):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    initial_api_payload = {
        "data": {
            "type": "employee_profile",
            "id": profile_id,
            "version_type": "1",
            "attributes": {
                "prid": "12345",
                "email": "old@mail.com",
                "location": "Office",
                "acc_type": "Staff",
            },
            "relationships": {
                "person": {
                    "data": {
                        "type": "ps_person",
                        "id": "11111111-1111-1111-1111-111111111111",
                    }
                },
                "legal_entity_ps": {
                    "data": {
                        "type": "legal_entity_ps",
                        "id": "22222222-2222-2222-2222-222222222222",
                    }
                },
            },
            "meta": {
                "created_at": "2024-03-15T12:00:00Z",
                "updated_at": "2024-03-20T14:30:00Z",
            },
        }
    }

    updated_api_payload = {
        "data": {
            "type": "employee_profile",
            "id": profile_id,
            "version_type": "2",
            "attributes": {
                "prid": "12345",
                "email": "new@mail.com",
                "location": "Remote",
                "acc_type": "Staff",
            },
            "relationships": {
                "person": {
                    "data": {
                        "type": "ps_person",
                        "id": "33333333-3333-3333-3333-333333333333",
                    }
                },
                "legal_entity_ps": {
                    "data": {
                        "type": "legal_entity_ps",
                        "id": "22222222-2222-2222-2222-222222222222",
                    }
                },
            },
            "meta": {
                "created_at": "2024-03-15T12:00:00Z",
                "updated_at": "2024-04-01T10:00:00Z",
            },
        }
    }

    old_checksum = _canonical_checksum(initial_api_payload)
    new_checksum = _canonical_checksum(updated_api_payload)
    assert old_checksum != new_checksum

    adapter_send = mocker.patch.object(
        requests.adapters.HTTPAdapter,
        "send",
        side_effect=[
            _make_response(200, initial_api_payload),
            _make_response(200, updated_api_payload),
            _make_response(200, {"status": "ok"}),
        ],
    )

    mocker.patch.object(
        requests.Session,
        "request",
        wraps=requests.Session.request,
    )

    api_client.get(EMPLOYEE_PROFILE_PATH.format(profile_id=profile_id))
    sync_resp = api_client.post(CRON_SYNC_PATH.format(profile_id=profile_id))

    assert sync_resp.status_code == 200

    assert adapter_send.call_count == 3

    fetched = updated_api_payload["data"]

    assert fetched["attributes"]["email"] == "new@mail.com"
    assert fetched["attributes"]["location"] == "Remote"
    assert fetched["version_type"] == "2"
    assert fetched["relationships"]["person"]["data"]["id"] == "33333333-3333-3333-3333-333333333333"

    now = datetime.now(timezone.utc)
    assert now


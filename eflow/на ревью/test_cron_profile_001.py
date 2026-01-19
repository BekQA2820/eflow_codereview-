import json
import uuid
import hashlib
import requests
from datetime import datetime, timezone
from unittest.mock import patch
from requests import Response

def _make_response(status: int, body: dict):
    r = Response()
    r.status_code = status
    r._content = json.dumps(body).encode("utf-8")
    r.headers["Content-Type"] = "application/vnd.api+json"
    r.headers["X-Request-ID"] = str(uuid.uuid4())
    return r

def _compute_checksum(payload: dict) -> str:
    canonical = {
        "type": payload["data"]["type"],
        "version_type": payload["data"]["version_type"],
        "attributes": payload["data"]["attributes"],
        "relationships": {
            k: {
                "data": v["data"]
            }
            for k, v in payload["data"]["relationships"].items()
        },
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def test_cron_profile_001_primary_insert_and_checksum(
    mocker,
    db_session,
    run_profile_cron,
):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    now = datetime.now(timezone.utc)

    external_payload = {
        "data": {
            "id": profile_id,
            "type": "employee_profile",
            "version_type": "v1",
            "attributes": {
                "prid": "PRID-001",
                "first_name": "Ivan",
                "last_name": "Petrov",
            },
            "relationships": {
                "person": {
                    "data": {"type": "person", "id": "person-123"}
                },
                "legal_entity": {
                    "data": {"type": "legal_entity", "id": "le-456"}
                },
            },
        }
    }

    expected_checksum = _compute_checksum(external_payload)

    resp = _make_response(200, external_payload)

    mocker.patch.object(
        requests.adapters.HTTPAdapter,
        "send",
        return_value=resp,
    )

    assert db_session.employee_profile.count() == 0

    run_profile_cron(profile_id=profile_id, fetched_at=now)

    rows = db_session.employee_profile.all()
    assert len(rows) == 1

    row = rows[0]
    assert row.profile_id == profile_id
    assert row.prid == "PRID-001"
    assert row.person_id == "person-123"
    assert row.legal_entity_ps_id == "le-456"
    assert row.checksum == expected_checksum
    assert row.checksum is not None
    assert row.fetched_at == now
    assert row.last_synced_at >= now
    assert row.created_at is not None
    assert row.updated_at is not None

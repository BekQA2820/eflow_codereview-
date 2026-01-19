import json
import hashlib
import uuid
import requests


def _canonical_checksum(data: dict) -> bytes:
    payload = {
        "type": data["type"],
        "version_type": data["version_type"],
        "attributes": data["attributes"],
        "relationships": {
            k: {
                "type": v["data"]["type"],
                "id": v["data"]["id"],
            }
            for k, v in data.get("relationships", {}).items()
            if "data" in v
        },
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).digest()


def test_cron_profile_004(mocker):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    base_data = {
        "type": "employee_profile",
        "id": profile_id,
        "version_type": "1",
        "attributes": {
            "prid": "12345",
            "email": "user@mail.test",
            "location": "Office",
            "acc_type": "Staff",
        },
        "relationships": {
            "person": {
                "data": {
                    "type": "ps_person",
                    "id": "11111111-1111-1111-1111-111111111111",
                }
            }
        },
        "meta": {
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
            "last_modified_by": "admin",
        },
    }

    meta_changed = json.loads(json.dumps(base_data))
    meta_changed["meta"]["updated_at"] = "2025-02-01T15:00:00Z"
    meta_changed["meta"]["last_modified_by"] = "system"

    checksum_before = _canonical_checksum(base_data)
    checksum_after = _canonical_checksum(meta_changed)

    assert checksum_before == checksum_after

    r = requests.Response()
    r.status_code = 200
    r._content = json.dumps({"data": meta_changed}).encode()
    r.headers = {
        "Content-Type": "application/json",
        "X-Request-ID": str(uuid.uuid4()),
    }

    mocker.patch.object(requests.adapters.HTTPAdapter, "send", return_value=r)

    assert checksum_after == checksum_before

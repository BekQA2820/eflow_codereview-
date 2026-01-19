import json
import uuid
import hashlib


def _canonical_payload(data: dict) -> dict:
    return {
        "type": data["type"],
        "version_type": data["version_type"],
        "attributes": data["attributes"],
        "relationships": {
            k: {"data": v["data"]}
            for k, v in data.get("relationships", {}).items()
            if "data" in v
        },
    }


def _checksum(data: dict) -> bytes:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).digest()


def test_cron_profile_005():
    profile_id = str(uuid.uuid4())

    data_v1 = {
        "type": "employee_profile",
        "id": profile_id,
        "version_type": "1",
        "attributes": {
            "prid": "123",
            "email": "user@test.local",
            "location": "Office",
            "acc_type": "Staff",
        },
        "relationships": {
            "person": {
                "data": {"type": "ps_person", "id": str(uuid.uuid4())}
            }
        },
        "links": {
            "self": "http://old-link"
        },
    }

    data_v2 = json.loads(json.dumps(data_v1))
    data_v2["links"]["self"] = "http://new-link"

    checksum_1 = _checksum(_canonical_payload(data_v1))
    checksum_2 = _checksum(_canonical_payload(data_v2))

    assert checksum_1 == checksum_2

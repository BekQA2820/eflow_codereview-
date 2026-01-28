import json
import uuid
import requests
from requests import Response
from unittest.mock import MagicMock

def test_cron_profile_001_initial_insert_and_checksum(
    mocker,
    employee_profile_repo,
    cron_profile_sync,
):
    profile_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    api_payload = {
        "data": {
            "id": profile_id,
            "type": "employee_profile",
            "version_type": "v1",
            "attributes": {
                "prid": "PRID-001",
                "email": "user@test.local",
                "location_code": "RU-MOW",
                "account_type_code": "EMPLOYEE",
            },
            "relationships": {
                "person": {"data": {"type": "person", "id": "person-1"}},
                "legal_entity": {"data": {"type": "legal_entity", "id": "le-1"}},
            },
        }
    }

    resp = Response()
    resp.status_code = 200
    resp._content = json.dumps(api_payload).encode("utf-8")
    resp.headers = {"Content-Type": "application/vnd.api+json"}

    mocker.patch.object(
        requests.Session,
        "request",
        return_value=resp,
    )

    employee_profile_repo.get_by_profile_id.return_value = None

    cron_profile_sync(profile_id)

    employee_profile_repo.insert.assert_called_once()
    args, kwargs = employee_profile_repo.insert.call_args

    record = kwargs["record"]
    assert record["profile_id"] == profile_id
    assert record["prid"] == "PRID-001"
    assert record["checksum"] is not None
    assert record["fetched_at"] is not None
    assert record["last_synced_at"] is not None

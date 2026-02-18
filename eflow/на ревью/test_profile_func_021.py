import json
import uuid
import re
import pytest
import allure

def _assert_uuid(v: str):
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
        v,
    )

@allure.epic("Profile")
@allure.feature("Functional")
@pytest.mark.integration 
def test_profile_func_021_get_reflects_latest_patch(api_client):
    trace_ids = [str(uuid.uuid4()) for _ in range(3)]
    etags = ['"etag-1"', '"etag-2"']

    body_initial = {
        "profile_uuid": "profile-id",
        "displayName": "Ivan",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z",
    }

    body_updated = {
        **body_initial,
        "displayName": "Ivan Updated",
        "updated_at": "2025-01-01T11:00:00Z",
    }

    # Сначала делаем GET запрос, чтобы получить исходные данные
    r_get = api_client.get("/api/v1/profiles/items/profile-id")
    assert r_get.status_code == 200
    assert r_get.headers["ETag"] == etags[0]

    # Затем PATCH запрос для обновления данных
    r_patch = api_client.patch(
        "/api/v1/profiles/items/profile-id",
        headers={"If-Match": etags[0]},
        json={"displayName": "Ivan Updated"},
    )
    assert r_patch.status_code == 200
    assert r_patch.headers["ETag"] == etags[1]

    # Получаем обновленные данные
    r_get_updated = api_client.get("/api/v1/profiles/items/profile-id")
    assert r_get_updated.status_code == 200
    assert r_get_updated.json()["displayName"] == "Ivan Updated"
    assert r_get_updated.headers["ETag"] == etags[1]
    _assert_uuid(r_get_updated.headers["X-Request-ID"])

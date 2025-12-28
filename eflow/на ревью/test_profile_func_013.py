import json
import uuid
import re

UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
DENY_FIELDS = {"internalId", "debugInfo", "stackTrace", "internalMeta"}


def test_profile_func_013_partial_update_no_mutation(mocker, api_client):
    """
    PROFILE FUNC 013
    Частичное обновление профиля без изменения других полей
    """

    trace_id = str(uuid.uuid4())

    initial_profile = {
        "name": "John",
        "surname": "Doe",
        "phone": "+123456789",
        "address": "123 Main St"
    }

    updated_profile = {
        "name": "John",
        "surname": "Doe"
    }

    # Simulate the GET response
    r_get = mocker.Mock()
    r_get.status_code = 200
    r_get.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "X-Request-ID": trace_id,
    }
    r_get.json.return_value = initial_profile
    mocker.patch("requests.get", return_value=r_get)

    # Simulate the PATCH request
    r_patch = mocker.Mock()
    r_patch.status_code = 200
    r_patch.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "Vary": "Authorization",
        "ETag": '"etag-v1"',
        "X-Request-ID": trace_id,
    }
    r_patch.json.return_value = updated_profile
    mocker.patch("requests.patch", return_value=r_patch)

    # Execute the test scenario
    r_patch_response = api_client.patch(
        "/api/v1/profiles/items/profile-1",
        json=updated_profile,
        headers={"If-Match": '"etag-v1"'}
    )

    # Verify PATCH response
    assert r_patch_response.status_code == 200
    assert r_patch_response.headers["Content-Type"] == "application/json"
    assert r_patch_response.headers["Cache-Control"] == "no-store"
    assert r_patch_response.headers["Vary"] == "Authorization"
    assert r_patch_response.headers["ETag"] == '"etag-v1"'

    data_patch = r_patch_response.json()
    assert data_patch["name"] == "John"
    assert data_patch["surname"] == "Doe"
    assert data_patch["phone"] == "+123456789"
    assert data_patch["address"] == "123 Main St"

    # Ensure no unexpected fields were mutated
    for field in DENY_FIELDS:
        assert field not in data_patch

    # Verify GET response after PATCH
    r_get_response = api_client.get(
        "/api/v1/profiles/items/profile-1",
        headers={"Authorization": "Bearer token"}
    )

    assert r_get_response.status_code == 200
    data_get = r_get_response.json()

    assert data_get["name"] == "John"
    assert data_get["surname"] == "Doe"
    assert data_get["phone"] == "+123456789"
    assert data_get["address"] == "123 Main St"

    # Check if PATCH did not alter other fields
    assert data_patch["phone"] == data_get["phone"]
    assert data_patch["address"] == data_get["address"]
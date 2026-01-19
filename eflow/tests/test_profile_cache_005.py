import json
import uuid


def test_profile_cache_005_cache_control_no_store(mocker, api_client):
    """
    PROFILE CACHE 005
    Проверка Cache-Control: no-store в ответах
    """

    trace_id = str(uuid.uuid4())

    profile_data = {
        "profile_id": "profile-123",
        "name": "Ivan",
        "surname": "Petrov",
        "phone": "+700000000",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
    }

    r = mocker.Mock()
    r.status_code = 200
    r.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": trace_id,
    }
    r.json.return_value = profile_data
    r.content = json.dumps(profile_data).encode()

    mocker.patch("requests.get", return_value=r)

    response = api_client.get("/api/v1/profiles/items/profile-123")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.headers["X-Request-ID"] == trace_id
    assert response.json() == profile_data
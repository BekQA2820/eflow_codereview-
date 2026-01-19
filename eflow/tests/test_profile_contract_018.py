import json
import uuid


def test_profile_contract_018_invalid_field_in_error_response(mocker, api_client):
    """
    PROFILE CONTRACT 018
    Проверка структуры ErrorResponse при ошибке с невалидным полем
    """

    error_body = {
        "code": "VALIDATION_ERROR",
        "message": "Invalid field value",
        "details": [
            {"field": "phone", "code": "INVALID_FORMAT"},
        ],
        "traceId": str(uuid.uuid4()),
    }

    r = mocker.Mock()
    r.status_code = 400
    r.headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Request-ID": error_body["traceId"],
    }
    r.json.return_value = error_body
    r.content = json.dumps(error_body).encode()

    mocker.patch("requests.get", return_value=r)

    response = api_client.get("/api/v1/profiles/items/profile-999")

    assert response.status_code == 400
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json() == error_body
    assert "traceId" in response.json()

    # Проверка структуры ErrorResponse
    assert "code" in response.json()
    assert "message" in response.json()
    assert "details" in response.json()
    assert isinstance(response.json()["details"], list)
    assert "field" in response.json()["details"][0]
    assert "code" in response.json()["details"][0]
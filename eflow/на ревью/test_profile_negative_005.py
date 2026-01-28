import pytest
import uuid

PROFILE_ID_B = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH_B = f"/api/v1/employee-profiles/{PROFILE_ID_B}"

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "<html", "requiredroles", "requiredpermissions",
    "email", "phone", "first_name", "last_name"
}


@pytest.mark.integration
def test_profile_negative_005_cross_user_access(api_client, auth_header):
    # auth_header принадлежит пользователю А
    # PATH_B указывает на профиль пользователя Б

    response = api_client.get(
        PATH_B,
        headers=auth_header
    )

    # Согласно Saved Info: Доступ к чужому ресурсу при валидном токене — это 403 Forbidden
    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()
    assert "ETag" not in response.headers

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert "traceId" in data

    # Проверка на отсутствие идентификаторов профиля Б в сообщении об ошибке (утечка существования)
    error_msg = data.get("message", "").lower()
    assert PROFILE_ID_B not in error_msg

    raw_low = response.text.lower()
    # Security Audit на наличие PII и технических полей
    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    assert "prid" not in raw_low
    assert "12345" not in raw_low
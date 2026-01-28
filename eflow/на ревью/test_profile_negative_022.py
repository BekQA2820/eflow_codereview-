import pytest
import uuid

TARGET_PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
PATH = f"/api/v1/employee-profiles/{TARGET_PROFILE_ID}"

DENY_FIELDS = {
    "internalflags", "internalid", "backendonly", "stacktrace",
    "exception", "requiredroles", "requiredpermissions", "privileges",
    "email", "phone", "first_name", "last_name", "3fa85f64"
}


@pytest.mark.integration
def test_profile_negative_022_rbac_deny_no_enumeration(api_client, auth_header):
    # Используется токен пользователя, у которого заведомо нет прав на TARGET_PROFILE_ID
    response = api_client.get(
        PATH,
        headers=auth_header
    )

    # Согласно Saved Info: Ошибки RBAC — это 403 Forbidden
    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"

    # Запрет кэширования ответов безопасности
    assert "no-store" in response.headers.get("Cache-Control", "").lower()
    assert "Authorization" in response.headers.get("Vary", "")

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert "message" in data
    assert "traceId" in data or "trace_id" in data

    # Проверка на отсутствие утечек (Data Leakage Protection)
    raw_low = response.text.lower()
    for field in DENY_FIELDS:
        # Важно: само значение TARGET_PROFILE_ID не должно быть в тексте ошибки
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Сообщение не должно подтверждать статус ресурса
    msg_low = data["message"].lower()
    assert "not found" not in msg_low
    assert "exist" not in msg_low
    assert "profile" not in msg_low

    # Проверка отсутствия старых ID
    assert "prid" not in raw_low
    assert "12345" not in raw_low
import pytest
import uuid

# Генерируем случайный UUID, которого гарантированно нет в БД
NON_EXISTENT_PROFILE_ID = "00000000-0000-0000-0000-000000000000"
# Константный UUID профиля другого пользователя
EXISTENT_OTHER_PROFILE_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

DENY_FIELDS = {
    "not found", "exists", "db", "mapping", "null", "none",
    "internalflags", "stacktrace", "exception", "<html", "backendonly"
}


@pytest.mark.integration
@pytest.mark.parametrize("target_id", [
    NON_EXISTENT_PROFILE_ID,
    EXISTENT_OTHER_PROFILE_ID
])
def test_profile_negative_031_masking_existence_on_forbidden(api_client, auth_header, target_id):
    path = f"/api/v1/employee-profiles/{target_id}"

    # Выполняем запрос с токеном пользователя без специальных разрешений
    response = api_client.get(
        path,
        headers=auth_header
    )

    # Согласно Saved Info: Любая попытка доступа к чужому профилю — это 403 Forbidden
    assert response.status_code == 403
    assert response.headers.get("Content-Type") == "application/json"
    assert "no-store" in response.headers.get("Cache-Control", "").lower()

    data = response.json()
    assert data["code"] == "FORBIDDEN"
    assert "message" in data
    assert "traceId" in data

    raw_low = response.text.lower()

    # Проверка маскирования: в ответе не должно быть самого UUID и признаков его (не)существования
    assert target_id.lower() not in raw_low

    for field in DENY_FIELDS:
        assert field not in raw_low
        assert field not in [str(k).lower() for k in data.keys()]

    # Сообщение должно быть максимально нейтральным и одинаковым для обоих случаев
    assert "access denied" in data["message"].lower()

    # Проверка отсутствия старых ID
    assert "prid" not in raw_low
    assert "12345" not in raw_low